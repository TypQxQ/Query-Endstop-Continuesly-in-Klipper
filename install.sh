#!/bin/bash

# Query Endstop Continuesly in Klipper
# Installation script
#
# Copyright (C) 2024  Andrei Ignat <andrei@ignat.se>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
#

#
# The responsibility of this script is to setup the Python extensions
# and configure the update processes.

# Set this to terminate on error.
set -e

# Get the root path of the repo, aka, where this script is executing
REPO_DIR=$(realpath $(dirname "$0"))

# This is where Klipper is installed
KLIPPER_HOME="${HOME}/klipper"

# This is where the extension are downloaded to, a subdirectory of the repo.
EXTENSION_PATH="${REPO_DIR}"

# This is where Moonraker is installed
MOONRAKER_HOME="${HOME}/moonraker"

# This is where Klipper config files are stored
KLIPPER_CONFIG_HOME="${HOME}/printer_data/config"

# This is where Klipper config files were stored before the 0.10.0 release
OLD_KLIPPER_CONFIG_HOME="${HOME}/klipper_config"

#
# Console Write Helpers
#
c_default=$(echo -en "\e[39m")
c_green=$(echo -en "\e[92m")
c_yellow=$(echo -en "\e[93m")
c_magenta=$(echo -en "\e[35m")
c_red=$(echo -en "\e[91m")

log_header()
{
    echo -e "${c_magenta}$1${c_default}"
}

log_important()
{
    echo -e "${c_yellow}$1${c_default}"
}

log_error()
{
    log_blank
    echo -e "${c_red}$1${c_default}"
    log_blank
}

log_info()
{
    echo -e "${c_green}$1${c_default}"
}

log_blank()
{
    echo ""
}

# 
# Logic to check if Klipper is installed
# 
check_klipper() {
    # Check if Klipper is installed
    log_blank
    log_header "Checking if Klipper is installed..."
    if [ "$(sudo systemctl list-units --full -all -t service --no-legend | grep -F "klipper.service")" ]; then
        log_important "${INFO}Klipper service found"
    else
        log_error "${ERROR}Klipper service not found! Please install Klipper first"
        exit -1
    fi
}

# 
# Logic to verify the home directories
# 
verify_home_dirs() {
    log_blank
    log_header "Verifying home directories..."
    if [ ! -d "${KLIPPER_HOME}" ]; then
        log_error "Klipper home directory (${KLIPPER_HOME}) not found. Use '-k <dir>' option to override"
        exit -1
    fi
    if [ ! -d "${KLIPPER_CONFIG_HOME}" ]; then
        if [ ! -d "${OLD_KLIPPER_CONFIG_HOME}" ]; then
            log_error "Klipper config directory (${KLIPPER_CONFIG_HOME} or ${OLD_KLIPPER_CONFIG_HOME}) not found. Use '-c <dir>' option to override"
            exit -1
        fi
        KLIPPER_CONFIG_HOME="${OLD_KLIPPER_CONFIG_HOME}"
    fi
    log_info "Klipper config directory (${KLIPPER_CONFIG_HOME}) found"

    if [ ! -d "${MOONRAKER_HOME}" ]; then
        log_error "Moonraker home directory (${MOONRAKER_HOME}) not found. Use '-m <dir>' option to override"
        exit -1
    fi    
}

restart_klipper()
{
    log_header "Restarting Klipper..."
    sudo systemctl restart klipper
}

restart_moonraker()
{
    log_header "Restarting Moonraker..."
    sudo systemctl restart moonraker
}

verify_ready()
{
    if [ "$EUID" -eq 0 ]; then
        log_error "This script must not run as root"
        exit -1
    fi
}

function nextfilename {
    local name="$1"
    if [ -d "${name}" ]; then
        printf "%s-%s" "${name%%.*}" "$(date '+%Y%m%d_%H%M%S')"
    else
        printf "%s-%s.%s-old" "${name%%.*}" "$(date '+%Y%m%d_%H%M%S')" "${name#*.}"
    fi
}

# 
# Logic to link the extension to Klipper
# 
link_extension()
{
    log_blank
    log_header "Linking extension files to Klipper..."
    ln -sf "${EXTENSION_PATH}/query_endstop_continuesly.py" "${KLIPPER_HOME}/klippy/extras/query_endstop_continuesly.py"
    log_info "Linked extension file: (query_endstop_continuesly.py)"
}

# 
# Logic to install the update manager to Moonraker
# 
install_update_manager() {
    log_blank
    log_header "Adding update manager to moonraker.conf"
    dest=${KLIPPER_CONFIG_HOME}/moonraker.conf
    if test -f "$dest"; then
        already_included=$(grep -c '\[update_manager Query-Endstop-Continuesly\]' "${dest}" || true)
        if [ "${already_included}" -eq 0 ]; then
            # Backup the original  moonraker.conf file
            next_dest="$(nextfilename "$dest")"
            log_info "Copying original moonraker.conf file to ${next_dest}"
            cp "${dest}" "${next_dest}"

            # Add the configuration to moonraker.conf
            echo "" >> "${dest}"    # Add a blank line
            echo "" >> "${dest}"    # Add a blank line
            echo -e "[update_manager Query-Endstop-Continuesly]" >> "${dest}"    # Add the section header
            echo -e "type: git_repo" >> "${dest}"
            echo -e "path: ${REPO_DIR}" >> "${dest}"
            echo -e "origin: https://github.com/TypQxQ/Query-Endstop-Continuesly-in-Klipper.git" >> "${dest}"
            echo -e "primary_branch: main" >> "${dest}"
            echo -e "install_script: install.sh" >> "${dest}"
            echo -e "managed_services: klipper" >> "${dest}"

            restart_moonraker
        else
            log_error "[update_manager Query-Endstop-Continuesly]] already exists in moonraker.conf - skipping installing it there"
        fi
    else
        log_error "moonraker.conf not found!"
    fi
}

# 
# Logic to install the configuration to Klipper
# 
install_klipper_config() {
    log_header "Adding configuration to printer.cfg"

    # Add configuration to printer.cfg if it doesn't exist
    dest=${KLIPPER_CONFIG_HOME}/printer.cfg
    if test -f "$dest"; then
        # Backup the original printer.cfg file
        next_dest="$(nextfilename "$dest")"
        log_info "Copying original printer.cfg file to ${next_dest}"
        cp "${dest}" "${next_dest}"

        # Add the configuration to printer.cfg
        # This example assumes that that both the server and the webcam stream are running on the same machine as Klipper
        already_included=$(grep -c '\[query_endstop_continuesly\]' "${dest}" || true)
        if [ "${already_included}" -eq 0 ]; then
            echo "" >> "${dest}"    # Add a blank line
            echo "" >> "${dest}"    # Add a blank line
            echo -e "[query_endstop_continuesly]" >> "${dest}"    # Add the section header

            log_info "Added query_endstop_continuesly configuration to printer.cfg"
            log_important "Please check the configuration in printer.cfg and adjust it as needed"
        else
            log_error "[query_endstop_continuesly] already exists in printer.cfg - skipping adding it there"
        fi
    else
        log_error "File printer.cfg file not found! Cannot add query_endstop_continuesly configuration. Do it manually."
    fi

    # Restart Klipper
    restart_klipper

}

# 
# Logic to ask a question and get a yes or no answer while displaying a prompt under installation
# 
prompt_yn() {
    while true; do
        read -n1 -p "
$@ (y/n)? " yn
        case "${yn}" in
            Y|y)
                echo "y" 
                break;;
            N|n)
                echo "n" 
                break;;
            *)
                ;;
        esac
    done
}

log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_blank
log_header "      Query Endstop Continuesly in Klipper"
log_blank
log_blank
log_important "Klipper module that adds a G-code command so Klipper will"
log_important "pause until specified endstop is in selected state,"
log_important "triggered or not triggered. Alternativley it can query a"
log_important "specified amount of times."
log_blank
log_info "Usage: $0 [-k <klipper_home_dir>] [-c <klipper_config_dir>] [-m <moonraker_home_dir>]"
log_blank
log_blank
log_important "This script will install the Query Endstop Continuesly in Klipper extension."
log_important "It will add the base configuration in printer.cfg and moonraker.conf."
log_blank
yn=$(prompt_yn "Do you want to continue?")
echo
case $yn in
    y)
        ;;
    n)
        log_info "You can run this script again later to install the "
        log_info "Query Endstop Continuesly in Klipper extension."
        log_blank
    exit 0
        ;;
esac



# Make sure we aren't running as root
verify_ready

# Check that Klipper is installed
check_klipper

# Check that the home directories are valid
verify_home_dirs

# Link the extension to Klipper
link_extension

# Install the update manager to Moonraker
install_update_manager

# Install the configuration to Klipper
install_klipper_config

log_blank
log_blank
log_important "Query Endstop Continuesly in Klipper extension is now installed."
log_important "Settings can be found in the printer.cfg file."
