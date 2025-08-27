import os
import re

import pandas as pd
from pathlib import Path
from typing import Any, Dict, List, Optional

from ntc_templates.parse import parse_output as ntc_parse_output
from neteye.lib.device_type_to_driver_mapping.device_type_to_driver_mapping import DeviceTypeToDriverMapping


ntc_template_platform_mapping = DeviceTypeToDriverMapping("ntc-template")


class NtcTemplateUtils:
    INDEX_FILE = (
        (os.environ.get("NET_TEXTFSM") + "/index") if os.environ.get("NET_TEXTFSM") else ""
    )
    TEMPLATE_EXTENSION = ".textfsm"
    ntc_template_index_df = pd.DataFrame()

    def __init__(self, custom_dir: Optional[str] = None):
        if self.INDEX_FILE and Path(self.INDEX_FILE).exists():
            self.ntc_template_index_df = pd.read_csv(
                self.INDEX_FILE,
                comment="#",
                skip_blank_lines=True,
                skipinitialspace=True,
            )
        self.custom_dir: Optional[str] = (
            str(Path(custom_dir)) if custom_dir and Path(custom_dir).exists() else None
        )

    def convert_template_to_platform(self, template):
        return self.ntc_template_index_df.loc[self.ntc_template_index_df["Template"] == template, "Platform"].values[0].strip()

    def convert_template_to_command(self, template):
        platform = self.convert_template_to_platform(template)
        template_lreplace = re.sub("^%s" % platform + "_", "", template)
        template_allreplace = re.sub("%s$" % self.TEMPLATE_EXTENSION, "", template_lreplace)
        return template_allreplace.replace("_", " ")

    def get_command_list(self, platform):
        template_list = self.ntc_template_index_df.query("Platform == @platform")["Template"].values.tolist()
        return [self.convert_template_to_command(template) for template in template_list]

    def _lreplace(self, pattern, sub):
        return sub('^%s' % pattern, sub, self)

    def _rreplace(self, pattern, sub):
        return sub('%s$' % pattern, sub, self)

    def parse(self, device_type: str, command: str, data: str) -> List[Dict[str, Any]]:
        """Parse Command output using ntc-templates with custom-overrides-first logic.

        Order:
        1) Try custom_dir (if set and exists)
        2) Fallback to default ntc-templates resolution (NET_TEXTFSM / package)
        """
        platform = ntc_template_platform_mapping.mapping_dict.get(device_type, device_type)

        # 1) Try custom directory first
        if self.custom_dir and Path(self.custom_dir).exists():
            try:
                return ntc_parse_output(
                    platform=platform,
                    command=command,
                    data=data,
                    template_dir=self.custom_dir,
                )
            except Exception:
                # Fall through to default resolution
                pass

        # 2) Default resolution (env NET_TEXTFSM or package)
        return ntc_parse_output(platform=platform, command=command, data=data)
