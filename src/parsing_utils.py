import logging
import os
from typing import Any, Dict, List, Optional, Union

from ntc_templates.parse import parse_output as ntc_parse_output, ParsingException
import ttp

# Import Genie (assuming it's installed)
try:
    from genie import testbed
    from genie.libs import parser as genie_parser

    GENIE_AVAILABLE = True
except ImportError:
    GENIE_AVAILABLE = False

# Path to the templates directory
# Adjust this path based on where parsing_utils.py is relative to the project root
TEMPLATES_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "parsing-templates"
)
TTP_TEMPLATES_DIR = os.path.join(TEMPLATES_DIR, "ttp")
TEXTFSM_TEMPLATES_DIR = os.path.join(TEMPLATES_DIR, "textfsm")

logger = logging.getLogger(__name__)


def load_ttp_template(template_name: str) -> Optional[str]:
    """Loads a TTP template from the templates/ttp directory."""
    template_path = os.path.join(TTP_TEMPLATES_DIR, f"{template_name}.txt")
    if os.path.exists(template_path):
        with open(template_path, "r") as f:
            return f.read()
    return None


def parse_cli_output(
    command: str,
    raw_output: str,
    device_type: str,  # Our custom OOP device type (e.g., 'cisco_ios_router', 'cisco_ios_switch')
    netmiko_device_type: str,  # The generic Netmiko device type (e.g., 'cisco_ios', 'juniper_junos')
) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Attempts to parse CLI output using multiple methods in a prioritized order:
    1. TextFSM (via Netmiko's built-in parsing)
    2. TTP
    3. Genie (placeholder)
    """
    # Attempt 1: TextFSM parsing using ntc_templates.parse.parse_output (official templates)
    try:
        logger.debug(
            f"TextFSM parsing (official) - netmiko_device_type: {netmiko_device_type}, command: {command}"
        )
        logger.debug(
            f"Trying to parse this raw_output {raw_output}"
        )
        parsed_data = ntc_parse_output(
            platform=netmiko_device_type, command=command, data=raw_output, try_fallback=True, template_dir=TEXTFSM_TEMPLATES_DIR
        )

        if parsed_data:
            logger.debug(f"TextFSM parsing (official) succeeded for command '{command}'.")
            return parsed_data

    except ParsingException as e:
        if "No template found" in str(e):
            logger.debug(
                f"TextFSM template not found for command '{command}' in official templates. Trying custom templates."
            )
        else:
            logger.error(
                f"TextFSM parsing (official) failed for command '{command}': {type(e).__name__}: {e}"
            )
    except Exception as e:
        logger.error(
            f"TextFSM parsing (official) failed for command '{command}': {type(e).__name__}: {e}"
        )

    # Attempt 2: TTP Parsing
    ttp_template_name = f"{netmiko_device_type}_{command.replace(' ', '_').replace('|', '_').replace('-', '_')}"
    ttp_template = load_ttp_template(ttp_template_name)

    if ttp_template:
        try:
            parser = ttp(data=raw_output, template=ttp_template)
            parser.parse()
            result = parser.result(structure="flat_list")

            if result and result[0]:
                if isinstance(result[0], list) and result[0]:
                    logger.debug(f"TTP parsing succeeded for command '{command}'.")
                    return result[0]
                elif isinstance(result[0], dict):
                    logger.debug(f"TTP parsing succeeded for command '{command}'.")
                    return [result[0]]
        except Exception as e:
            logger.error(
                f"TTP parsing failed for command '{command}': {type(e).__name__}: {e}"
            )

    # Attempt 3: Genie Parsing (Placeholder - requires more setup)
    if GENIE_AVAILABLE:
        try:
            # Placeholder for Genie parsing logic
            # parsed_data = genie_parse(command, raw_output, netmiko_device_type) # Assuming genie_parse exists
            # if parsed_data:
            #     logger.debug(f"Genie parsing succeeded for command '{command}'.")
            #     return parsed_data
            pass
        except Exception as e:
            logger.error(
                f"Genie parsing failed for command '{command}': {type(e).__name__}: {e}"
            )

    logger.warning(
        f"No parser succeeded for command '{command}'. Returning empty list."
    )
    return []
