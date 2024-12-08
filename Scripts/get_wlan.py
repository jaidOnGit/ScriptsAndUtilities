import os
import re
import subprocess
import argparse
import wifi_qrcode_generator as qr

def parse_script_arguments():
    parser = argparse.ArgumentParser(
        description="Process arguments custom defined"
    )
    # optional arguments
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='enable verbose output'
    )

    # parser.add_argument(
    #     '-arg1',
    #     type=str,
    #     help='first arg to script'
    # )

    # dynamic keyword arguments
    parsed_args, unknown_args = parser.parse_known_args()
    setattr(
        parsed_args,
        '__dynamic_settings__',
        {}
    )
    if len(unknown_args) > 0:
        
        for kvpair in unknown_args:
            if '=' in kvpair:
                k, v = kvpair.split('=', maxsplit=1)
                parsed_args.__dynamic_settings__[k] = str(v)
            else:
                print(f"Warning: Ignoring invalid argument '{kvpair}'")
    # print(parsed_args)
    return parsed_args

# wlan utility
class WLAN_utility:
    def __init__(self):
        self.win_wlan_commands = {
            'showPass': 'netsh wlan show profile name="SSID" key=clear',
            'wlanDrivers': 'netsh wlan show drivers',
            'wlanCapabilities': 'netsh wlan show capabilities',
            'wlanSaved': 'netsh wlan show profiles',
            'wlanRemove': 'netsh wlan delete profile name=[PROFILENAME]',
            'wlanRemoveAll': 'netsh wlan delete profiles',
            'wlanExport': 'netsh wlan export profile name="SSID" key=clear folder=WlanExportFolder',
            'wlanImport': 'netsh wlan add profile filename="ABSOLUTEPATH.XML" interface="INTERFACENAME"',
            'wlanAdapterReport': 'netsh wlan show wlanreport'
        }
        self.hideSSID_list = []
        self.set_hidden_ssid_list(ssid='Einstein')
        self.saved_wlans = {}

    def set_hidden_ssid_list(self, ssid='Einstein'):
        self.hideSSID_list.append(ssid)
    
    def get_wlan_password(self, ssid_name):
        return re.findall(
            r"Key Content\s*:\s*(\w+)",
            self.command_prompt(command=self.win_wlan_commands.get('showPass').replace('SSID', ssid_name)),
            flags=re.IGNORECASE
        )[0]

    def get_saved_wlan(self):
        saved_wlan = re.findall(
            r"All User Profile\s*:\s*(.+)",
            self.command_prompt(command=self.win_wlan_commands.get("wlanSaved")),
            flags=re.IGNORECASE
        )
        for ssid in saved_wlan:
            ssid = ssid.replace('\r', '')
            if ssid not in self.hideSSID_list:
                wpass = self.get_wlan_password(ssid_name=ssid)
                if len(wpass) > 0:
                    self.saved_wlans.update({
                        ssid: wpass
                    })
        return self.saved_wlans

    def command_prompt(self, command='whoami'):
        try:
            stdout = subprocess.check_output(command, shell=True)
            return stdout.decode('utf-8')
        except subprocess.CalledProcessError as subprocess_exception:
            print(subprocess_exception)
            return ''

    def get_QR(self, **kwargs):
        WPASS = self.get_wlan_password(ssid_name=kwargs.get('SSID'))
        qr_code = qr.wifi_qrcode(
            kwargs.get('SSID'),
            hidden=False,
            authentication_type='WPA',
            password=WPASS
        )
        qr_code_img = qr_code.make_image()
        qr_path = os.path.join(os.path.dirname(__file__), f'qr_{kwargs.get("SSID")}.png')
        qr_code_img.save(qr_path)
        if kwargs.get('show', False):
            os.system(f'start {qr_path}')  # This will open the QR code image on Windows



def main():
    script_args = parse_script_arguments()
    wlan_utils = WLAN_utility()
    ssid = script_args.__dynamic_settings__.get('--ssid')
    show_QR = script_args.__dynamic_settings__.get('--qr', False)
    if ssid:
        print(wlan_utils.get_wlan_password(ssid_name=ssid))
        wlan_utils.get_QR(SSID=ssid, show=bool(show_QR))
    else:
        print("SSID not provided -- Displaying all saved ssid details from this host")
        print(wlan_utils.get_saved_wlan())

if __name__ == "__main__":
    main()
