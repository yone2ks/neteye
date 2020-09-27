from ntc_template_utils import NtcTemplateUtils

ntc_template_utils = NtcTemplateUtils()
print(ntc_template_utils.ntc_template_index_df.columns.values)
print(ntc_template_utils.convert_template_to_platform("cisco_xr_show_bgp_neighbors.template"))
print(ntc_template_utils.convert_template_to_command("cisco_xr_show_bgp_neighbors.template"))
print(ntc_template_utils.get_command_list("cisco_xr"))
