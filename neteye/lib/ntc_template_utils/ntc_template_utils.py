import os
import re

import pandas as pd


class NtcTemplateUtils:
    INDEX_FILE = os.environ["NET_TEXTFSM"] + "/index"
    TEMPLATE_EXTENSION = ".textfsm"
    ntc_template_index_df = pd.DataFrame()

    def __init__(self):
        self.ntc_template_index_df = pd.read_csv(self.INDEX_FILE, comment="#", skip_blank_lines=True, skipinitialspace=True)

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
