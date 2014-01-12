from os import system


class Py3status:
    """
    This module allows activation and deactivation
    of DPMS (Display Power Management Signaling)
    by clicking on 'DPMS' in the status bar.

    Written and contributed by @tasse:
        Andre Doser <dosera AT tf.uni-freiburg.de>
    """
    def __init__(self):
        """
        Detect current state on start.
        """
        self.run = system('xset -q | grep -iq "DPMS is enabled"') == 0

    def dpms(self, i3status_output_json, i3status_config):
        """
        Display a colorful state of DPMS.
        """
        result = {
            'full_text': 'DPMS',
            'name': 'dpms'
        }
        if self.run:
            result['color'] = i3status_config['color_good']
        else:
            result['color'] = i3status_config['color_bad']
        return (0, result)

    def on_click(self, json, i3status_config, event):
        """
        Enable/Disable DPMS on left click.
        """
        if event['button'] == 1:
            if self.run:
                self.run = False
                system("xset -dpms")
            else:
                self.run = True
                system("xset +dpms")
            system("killall -USR1 py3status")
