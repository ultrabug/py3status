.. _user-contributed-conf-examples:

User Contributed Configuration Examples
=======================================

Here you can find community contributed configuration examples to help you get started with some modules or benefit from the tricks of other hackers!

Ultrabug's configuration examples
---------------------------------

.. code-block:: none

    # one button for bluetooth on/off
    bluetooth {
    	format = ""
    	on_click 1 = "exec bluetoothctl power on"
    	on_click 3 = "exec bluetoothctl power off"
    }
    
    # I use pulseausio and I like to control the sinks and sources 
    # directly from my bar!
    #
    # These modules allow me to not only control the volume of the given
    # devices but to also switch the sound output from one to another
    
    # This is the speakers from my laptop, I can switch sound to it
    # on middle click
    volume_status speakers {
    	command = "pactl"
        device = "alsa_output.pci-0000_00_1f.3.analog-stereo"
    	format = "💻{percentage}%"
    	format_muted = "💻{percentage}%"
        on_click 2 = "exec pactl set-default-sink alsa_output.pci-0000_00_1f.3.analog-stereo"
    	thresholds = [(0, 'bad'), (5, 'degraded'), (10, 'good')]
    }
    
    # I plugin a USB headset, it appears, I can switch default sound to
    # it while controlling its volume output. When disconnected, it
    # disappears from the bar
    volume_status sennheiser {
    	command = "pactl"
        device = "alsa_output.usb-Sennheiser_"
    	format = "[\?if=!percentage=? 🎧{percentage}%]"
    	format_muted = '🎧{percentage}%'
        on_click 2 = "exec pactl set-default-sink alsa_output.usb-Sennheiser_Sennheiser_SC_160_USB_A002430203100377-00.analog-stereo"
    	thresholds = [(0, 'bad'), (5, 'degraded'), (10, 'good')]
    }
    
    # I also can activate a remote bluetooth speaker by clicking on this,
    # when it connects the sound percentage appears, I can switch output
    # to it by middle clicking or disconnect it by right clicking
    volume_status bose {
    	command = "pactl"
        device = "bluez_sink..+.a2dp_sink"
    	format = "[\?if=!percentage=? 📻{percentage}%][\?if=percentage=? 📻]"
    	format_muted = '📻{percentage}%'
        on_click 2 = "exec pactl set-default-sink bluez_sink.2C_41_A1_Z7_FA_C2.a2dp_sink"
    	on_click 1 = "exec bluetoothctl connect 2C:41:A1:Z7:FA:C2"
    	on_click 3 = "exec bluetoothctl disconnect 2C:41:A1:Z7:FA:C2"
    	thresholds = [(0, 'bad'), (5, 'degraded'), (10, 'good')]
    	max_volume = 200
    }
    
    # I also control the default microphone volume from the bar
    # and can mute it
    volume_status mic {
        format = '🎙️{percentage}%'
        format_muted = '🎙️{percentage}%'
    	button_down = 5
    	button_mute = 1
    	button_up = 4
    	is_input = true
    	thresholds = [(0, 'bad'), (10, 'degraded'), (20, 'good')]
    }
    
    # DMPS status shows as a red/green screen
    dpms {
    	icon_off = ""
    	icon_on = ""
    }
    
    # cycling time in meaningful cities
    group tz {
    	cycle = 10
    	format = "{output}"
    	#click_mode = "button"
    
    	tztime la {
    		format = "🌉%H:%M"
    		timezone = "America/Los_Angeles"
    	}
    
    	tztime ny {
    		format = "🗽%H:%M"
    		timezone = "America/New_York"
    	}
    
    	tztime du {
    		format = "🕌%H:%M"
    		timezone = "Asia/Dubai"
    	}
    
    	tztime tw {
    		format = "⛩️%H:%M"
    		timezone = "Asia/Taipei"
    	}
    
        tztime in {
    		format = "🛕%H:%M"
    		timezone = "Asia/Kolkata"
    	}
    }

CorruptCommit's configuration examples
--------------------------------------

.. code-block:: none

    # If I had time, I would make these proper modules.  Free feel to make them
    # if you got time.

    # weather without needing an API key
    getjson wttr {
    	url = "https://wttr.in/Paris?format=j1"
    	format = "{current_condition-0-FeelsLikeC}° {current_condition-0-weatherDesc-0-value}"
    	cache_timeout = 3600
    }
    
    # example output
    # 6° Partly cloudy

    # SABnzbd status
    getjson sabnzbd {
    	url = "https://sabnzbd.example.com/api?mode=queue&apikey=000000000&output=json"
    	format = "SABnzbd: {queue-status}"
    	cache_timeout = 60
    }
    # example output
    # SABnzbd: Idle
    
    

