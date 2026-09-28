#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qidi Plus 5 - Neopixel Driver Patch
Adds hardware animation timers for CanhsatHinhsu & DiscoDance effects,
and prevents UI screen sleep from turning off RGB underbed LED.
"""

import sys
import os
import shutil

NEOPIXEL_PATH = "/home/qidi/klipper/klippy/extras/neopixel.py"
BACKUP_PATH = "/home/qidi/klipper/klippy/extras/neopixel.py.bak_rgbmod"

def apply_patch():
    if not os.path.exists(NEOPIXEL_PATH):
        print(f"Error: {NEOPIXEL_PATH} not found!")
        sys.exit(1)

    # 1. Create backup if not already present
    if not os.path.exists(BACKUP_PATH):
        shutil.copyfile(NEOPIXEL_PATH, BACKUP_PATH)
        print(f"Created backup: {BACKUP_PATH}")
    else:
        print(f"Existing backup found at: {BACKUP_PATH}")

    with open(BACKUP_PATH, 'r', encoding='utf-8') as f:
        code = f.read()

    # 2. Patch __init__ for reactor timer
    patch_init = """        self.printer.register_event_handler("ui:sleep", self._handle_ui_event)
        self.reactor = printer.get_reactor()
        self.xanhdo_timer = None
        self.xanhdo_step = 0
        self.xanhdo_cycles = 0"""

    target_init = '        self.printer.register_event_handler("ui:sleep", self._handle_ui_event)'
    if target_init in code:
        code = code.replace(target_init, patch_init, 1)

    # 3. Patch _handle_ready for timer registration
    patch_ready = """    def _handle_ready(self):
        \"\"\"系统就绪后的默认灯效\"\"\"
        if self.xanhdo_timer is None:
            self.xanhdo_timer = self.reactor.register_timer(self._xanhdo_timer_event, self.reactor.NEVER)"""

    target_ready = '    def _handle_ready(self):\n        """系统就绪后的默认灯效"""'
    if target_ready in code:
        code = code.replace(target_ready, patch_ready, 1)

    # 4. Patch register_gcode
    old_gcode = """        gcode.register_command("NEOPIXEL_ENABLE", self.cmd_breath_enable,
            desc="呼吸灯使能: NEOPIXEL_ENABLE ENABLE=1/0")"""

    new_gcode = """        gcode.register_command("NEOPIXEL_ENABLE", self.cmd_breath_enable,
            desc="呼吸灯使能: NEOPIXEL_ENABLE ENABLE=1/0")
        gcode.register_command("NEOPIXEL_DISCODANCE", self.cmd_discodance,
            desc="Hiệu ứng Disco Dance chớp gầm kết hợp đèn thùng")
        gcode.register_command("NEOPIXEL_CANHSATHINHSU", self.cmd_canhsathinhsu,
            desc="Hiệu ứng Cảnh Sát Hình Sự chớp kép Xanh Đỏ")
        gcode.register_command("NEOPIXEL_XANHDO", self.cmd_canhsathinhsu,
            desc="Alias cho CanhsatHinhsu")"""

    if old_gcode in code:
        code = code.replace(old_gcode, new_gcode, 1)

    # 5. Add cancel calls to manual controls
    for target in ["    def cmd_breath_mode(self, gcmd):",
                   "    def cmd_breath_enable(self, gcmd):",
                   "    def cmd_breath_off(self, gcmd):"]:
        if target in code and "self._cancel_xanhdo()" not in code.split(target)[1][:100]:
            code = code.replace(target, target + "\n        self._cancel_xanhdo()", 1)

    # 6. Screen sleep keep-alive
    old_sleep = """        if screen == 0:
            self._get_preset(0, force=True) # 强制设为 0 模式，确保状态同步
            self._send_led_cmd(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            action_desc = "LED OFF (Smart Energy Saving)\""""

    new_sleep = """        if screen == 0:
            action_desc = "KEEP ALIVE: Screen Sleep Ignored for RGB\""""

    if old_sleep in code:
        code = code.replace(old_sleep, new_sleep, 1)

    # 6b. Set printing progress to Mode 2 (Deep Pink Breathing, remaining LEDs OFF)
    old_status_printing = "'printing':    (1, self._get_progress_count(), 0),"
    new_status_printing = "'printing':    (2, self._get_progress_count(), 0), # Deep Pink Breathing Progress"
    if old_status_printing in code:
        code = code.replace(old_status_printing, new_status_printing, 1)

    old_preset_2 = "2: (180, 255, 255, 0, 5000, 20),"
    new_preset_2 = "2: (255, 0, 128, 0, 2000, 25),      # BREATH: Deep Pink Breathing Progress"
    if old_preset_2 in code:
        code = code.replace(old_preset_2, new_preset_2, 1)

    old_prog = "self._send_led_cmd(1, 255, 255, 255, 0, current_count, 0, 0, 0, 0)"
    new_prog = "self._send_led_cmd(2, 255, 0, 128, 0, current_count, 0, 0, 2000, 25)"
    if old_prog in code:
        code = code.replace(old_prog, new_prog, 1)

    # 7. Add core methods
    new_methods = """    def _set_caselight(self, val):
        caselight = self.printer.lookup_object('output_pin caselight', None)
        if caselight is not None:
            try:
                systime = self.reactor.monotonic()
                print_time = caselight.mcu_pin.get_mcu().estimated_print_time(systime)
                caselight.mcu_pin.set_digital(print_time, 1 if val else 0)
                caselight.last_value = 1.0 if val else 0.0
            except Exception as e:
                logging.exception("Error setting caselight: %s", str(e))

    def _cancel_xanhdo(self):
        if self.xanhdo_timer is not None:
            self.reactor.update_timer(self.xanhdo_timer, self.reactor.NEVER)
        if getattr(self, 'with_caselight', False) and hasattr(self, 'orig_caselight'):
            self._set_caselight(self.orig_caselight)

    def _set_split_colors(self, left_color, right_color):
        # 25 LEDs: LEDs 0..11 là Nửa Trái (12 bóng), LEDs 12..24 là Nửa Phải (13 bóng)
        led_state = []
        for i in range(self.num_leds):
            if i < 12:
                led_state.append(left_color)
            else:
                led_state.append(right_color)
        with self.mutex:
            self.update_color_data(led_state)
            self.send_data()

    def cmd_discodance(self, gcmd):
        self._start_police_effect(with_caselight=True, name="DISCO DANCE")

    def cmd_canhsathinhsu(self, gcmd):
        self._start_police_effect(with_caselight=False, name="POLICE STROBE")

    def cmd_xanhdo(self, gcmd):
        self.cmd_canhsathinhsu(gcmd)

    def _start_police_effect(self, with_caselight, name):
        self._cancel_xanhdo()
        self.auto_mode_enabled = False
        self._send_led_cmd(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        self.with_caselight = with_caselight
        if with_caselight:
            caselight = self.printer.lookup_object('output_pin caselight', None)
            self.orig_caselight = caselight.last_value if caselight is not None else 1.0
        
        self.xanhdo_step = 0
        self.xanhdo_cycles = 0
        self.effect_name = name
        gcode = self.printer.lookup_object('gcode')
        gcode.respond_info(f"STARTING {name}: 10 double-strobe cycles...")
        waketime = self.reactor.monotonic()
        if self.xanhdo_timer is not None:
            self.reactor.update_timer(self.xanhdo_timer, waketime)

    def _xanhdo_timer_event(self, eventtime):
        gcode = self.printer.lookup_object('gcode')
        try:
            sub = self.xanhdo_step
            wc = getattr(self, 'with_caselight', False)

            # Step 0: 0.2s: Left: BLUE | Right: OFF | (Chamber: OFF if Disco)
            if sub == 0:
                self._set_split_colors((0.0, 0.0, 1.0), (0.0, 0.0, 0.0))
                if wc: self._set_caselight(0)
                self.xanhdo_step = 1
                return eventtime + 0.2

            # Step 1: 0.05s: Pause OFF
            elif sub == 1:
                self._set_split_colors((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
                if wc: self._set_caselight(0)
                self.xanhdo_step = 2
                return eventtime + 0.05

            # Step 2: 0.2s: Left: BLUE | Right: OFF | (Chamber: ON if Disco)
            elif sub == 2:
                self._set_split_colors((0.0, 0.0, 1.0), (0.0, 0.0, 0.0))
                if wc: self._set_caselight(1)
                self.xanhdo_step = 3
                return eventtime + 0.2

            # Step 3: 0.05s: Pause OFF
            elif sub == 3:
                self._set_split_colors((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
                if wc: self._set_caselight(0)
                self.xanhdo_step = 4
                return eventtime + 0.05

            # Step 4: 0.2s: Left: OFF | Right: RED | (Chamber: OFF if Disco)
            elif sub == 4:
                self._set_split_colors((0.0, 0.0, 0.0), (1.0, 0.0, 0.0))
                if wc: self._set_caselight(0)
                self.xanhdo_step = 5
                return eventtime + 0.2

            # Step 5: 0.05s: Pause OFF
            elif sub == 5:
                self._set_split_colors((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
                if wc: self._set_caselight(0)
                self.xanhdo_step = 6
                return eventtime + 0.05

            # Step 6: 0.2s: Left: OFF | Right: RED | (Chamber: ON if Disco)
            elif sub == 6:
                self._set_split_colors((0.0, 0.0, 0.0), (1.0, 0.0, 0.0))
                if wc: self._set_caselight(1)
                self.xanhdo_step = 7
                return eventtime + 0.2

            # Step 7: 0.05s: Pause OFF -> Completed 1 cycle (1.0s)
            elif sub == 7:
                self._set_split_colors((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
                if wc: self._set_caselight(0)
                self.xanhdo_cycles += 1
                gcode.respond_info(f"[{getattr(self, 'effect_name', '')}] Cycle [{self.xanhdo_cycles}/10] complete")
                if self.xanhdo_cycles >= 10:
                    self.xanhdo_step = 8
                else:
                    self.xanhdo_step = 0
                return eventtime + 0.05

            # Step 8: Completed 10 cycles -> Restore chamber light & return to Rainbow Wave
            elif self.xanhdo_step == 8:
                if wc and hasattr(self, 'orig_caselight'):
                    self._set_caselight(self.orig_caselight)
                self.auto_mode_enabled = True
                preset = self._get_preset(4, force=True)
                self._send_led_cmd(4, *preset[:4], self.num_leds, 0, 0, *preset[4:])
                gcode.respond_info(f"🌈 [DONE] {getattr(self, 'effect_name', '')} finished, returning to Rainbow Wave!")
                return self.reactor.NEVER

        except Exception as e:
            logging.exception("Error in police/disco timer: %s", str(e))
        return self.reactor.NEVER
"""

    target_eof = "def load_config_prefix(config):"
    if target_eof in code and "_set_caselight" not in code:
        code = code.replace(target_eof, new_methods + "\n" + target_eof, 1)

    # 8. Write to temp file & verify syntax
    tmp_path = "/tmp/neopixel_modded.py"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        f.write(code)

    res = os.system(f"python3 -m py_compile {tmp_path}")
    if res != 0:
        print("Compilation failed! Patch aborted, original file preserved.")
        sys.exit(1)

    # 9. Overwrite neopixel.py
    shutil.copyfile(tmp_path, NEOPIXEL_PATH)
    print("Patch applied and compiled successfully!")

if __name__ == "__main__":
    apply_patch()
