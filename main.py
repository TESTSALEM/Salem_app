import kivy
from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, DictProperty, ListProperty, ObjectProperty, BooleanProperty
from kivy.core.window import Window
from kivy.animation import Animation
import json
import os
import random
from kivy.factory import Factory
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from datetime import datetime, timedelta, date

kivy.require('1.9.0')

# --- الثوابت والإعدادات العامة ---
SCORE_FILE = 'high_score.json'
ACHIEVEMENTS_FILE = 'achievements.json'
CURRENCY_FILE = 'currency.json'
STATS_FILE = 'stats.json'

# إعدادات اللعب الأساسية
TIME_LIMIT = 10.0
BASE_PENALTY_TIME = 1.0
COINS_PER_CLICK = 0.5
SURVIVAL_START_TIME = 5.0
SURVIVAL_TIME_BONUS = 0.5
REACTION_TIME_WINDOW = 0.8  # وقت النقر المتاح في وضع رد الفعل

# --- تعريف الألوان لوضع رد الفعل ---
REACTION_COLORS = {
    "RED": [0.8, 0.2, 0.2, 1],
    "GREEN": [0.2, 0.8, 0.2, 1],
    "BLUE": [0.2, 0.2, 0.8, 1],
}

# --- تعريف الإحصائيات الافتراضية ---
DEFAULT_STATS = {
    "total_clicks": 0,
    "total_wrong_taps": 0,
    "total_games_played": 0,
    "survival_high_time": 0.0,
    "accuracy_high_score": 0,
    "reaction_high_score": 0
}

# --- تعريف الإنجازات (Data Model) ---
ACHIEVEMENTS_DATA = {
    "speed_demon": {"name": "Speed Demon", "description": "Achieve 50 clicks in one game.", "unlocked": False, "target": 50},
    "focused": {"name": "Focused Tapper", "description": "Win a game without hitting the 'DON'T TAP' button.", "unlocked": False},
    "veteran": {"name": "Game Veteran", "description": "Play 10 games.", "unlocked": False, "count_key": "total_games", "target": 10}
}

# --- تعريف عناصر المتجر والتخصيص والترقيات ---
SHOP_ITEMS = [
    # الثيمات (Themes)
    {"id": "default", "name": "Default Theme", "price": 0, "type": "theme", "color": [0.0, 0.0, 0.0, 1]},
    {"id": "bg_blue", "name": "Blue Theme", "price": 50, "type": "theme", "color": [0.1, 0.1, 0.5, 1]},
    {"id": "bg_red", "name": "Red Theme", "price": 75, "type": "theme", "color": [0.5, 0.1, 0.1, 1]},
    {"id": "bg_green", "name": "Green Theme", "price": 100, "type": "theme", "color": [0.1, 0.5, 0.1, 1]},
    # سيتم فتح هذا الثيم كمكافأة يوم 7 (إن لم يكن موجودًا)
    {"id": "bg_premium", "name": "Premium Theme", "price": 0, "type": "theme", "color": [0.6, 0.2, 0.8, 1]}, 

    # الترقيات (Upgrades)
    {"id": "up_click1", "name": "Click Multiplier +0.1", "price": 150, "type": "upgrade", "effect": {"multiplier_increase": 0.1}, "level": 1, "max_level": 5},
    {"id": "up_penalty1", "name": "Penalty Time -0.1s", "price": 200, "type": "upgrade", "effect": {"penalty_reduction": 0.1}, "level": 1, "max_level": 3},
]

# --- مكافآت سلسلة الأيام (Streak 7 أيام) ---
# ترتيب المكافآت لليوم 1..7
DAILY_STREAK_REWARDS = [20, 30, 40, 60, 80, 100, 150]  # اليوم السابع مكافأة كبيرة + ثيم

# --- دوال حفظ وتحميل البيانات ---

def load_data(filename, default_data):
    """تحميل البيانات من ملف JSON أو إرجاع البيانات الافتراضي."""
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            try:
                if os.path.getsize(filename) == 0:
                    return default_data.copy() if isinstance(default_data, dict) else default_data
                data = json.load(f)
                return data
            except (json.JSONDecodeError):
                return default_data.copy() if isinstance(default_data, dict) else default_data
    return default_data.copy() if isinstance(default_data, dict) else default_data

def save_data(filename, data):
    """حفظ البيانات إلى ملف JSON."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

# --- عنصر المتجر المخصص ---
class ShopItem(BoxLayout):
    """عنصر مخصص لعرض عناصر المتجر في قائمة التمرير."""
    item_id = StringProperty('')
    item_name = StringProperty('Item Name')
    item_price = NumericProperty(0)
    item_type = StringProperty('')
    item_color = ListProperty([0, 0, 0, 1]) # لون الثيم
    display_status = StringProperty('Buy') # حالة العرض (Buy/Equip/Max)
    
    def on_press_action(self):
        """يستدعي دالة الشراء أو التفعيل في الشاشة الأصلية (ShopScreen)."""
        # الوصول إلى ShopScreen: ShopItem -> GridLayout -> ScrollView -> BoxLayout -> ShopScreen
        # نحتاج إلى السفر 4 مستويات للأعلى
        shop_screen = self.parent.parent.parent.parent
        
        # التأكد من أن الشاشة موجودة وأن لديها الدالة المطلوبة
        if shop_screen and hasattr(shop_screen, 'purchase_or_activate'):
            # يرسل الـ ID، السعر، والنوع إلى دالة المعالجة الرئيسية
            shop_screen.purchase_or_activate(self.item_id, self.item_price, self.item_type)

Factory.register('ShopItem', cls=ShopItem)

# --- شاشات التطبيق ---

class MenuScreen(Screen):
    display_high_score = StringProperty("BEST SCORE: 0")
    display_achievements = StringProperty("Loading Achievements...")
    display_coins = StringProperty("Coins: 0")
    daily_indicator = StringProperty("")  # نص يظهر إن لم يتم جمع المكافأة اليوم
    
    def on_enter(self, *args):
        app = App.get_running_app()
        
        # إعادة تحميل البيانات
        app.game_data = load_data(ACHIEVEMENTS_FILE, {"total_games": 0, "achievements": {}})
        app.high_score = load_data(SCORE_FILE, {"high_score": 0}).get("high_score", 0)
        app.currency_data = load_data(CURRENCY_FILE, {"coins": 0, "unlocked_themes": ["default"], "upgrades": {}, "daily_reward": {"last_claim": "", "streak_day": 0, "last_claim_date": ""}})
        app.stats_data = load_data(STATS_FILE, DEFAULT_STATS)

        # إذا لم يكن هناك مفتاح daily_reward، أنشئه
        if "daily_reward" not in app.currency_data:
            app.currency_data["daily_reward"] = {"last_claim": "", "streak_day": 0, "last_claim_date": ""}

        # تحديث الواجهة
        self.display_high_score = f"BEST SCORE: {app.high_score}"
        self.check_daily_status()  # تحقق من حالة المكافأة اليومية (ولا تعطيها هنا إنما تعرض حالة)
        
        # تحديث قائمة الإنجازات
        achievements_text = "--- ACHIEVEMENTS ---\n"
        for key, data in ACHIEVEMENTS_DATA.items():
            is_unlocked = app.game_data.get('achievements', {}).get(key, {}).get('unlocked', False)
            status = "[color=33FF33]UNLOCKED[/color]" if is_unlocked else "[color=FF3333]LOCKED[/color]"
            achievements_text += f"{status}: {data['name']}\n"
        self.display_achievements = achievements_text

    def check_daily_status(self):
        """
        يتحقق ما إذا كان المستخدم مؤهلاً للحصول على مكافأة اليوم أم لا
        ويحدّث display_coins و daily_indicator.
        لا تقوم بجمع المكافأة هنا — فقط تعرض الحالة.
        """
        app = App.get_running_app()
        today_iso = date.today().isoformat()
        daily = app.currency_data.get("daily_reward", {"last_claim": "", "streak_day": 0, "last_claim_date": ""})
        last_claim_date = daily.get("last_claim_date", "")
        streak_day = daily.get("streak_day", 0)

        # تحديث عرض العملات بشكل افتراضي
        self.display_coins = f"Coins: {app.currency_data.get('coins', 0)}"

        if last_claim_date != today_iso:
            # المستخدم لم يجمع مكافأة اليوم بعد
            self.daily_indicator = f"Daily Reward Available! (Day {min(streak_day+1, 7)})"
        else:
            self.daily_indicator = "Daily Reward Collected Today."

    def go_to_daily_rewards(self):
        """ينتقل إلى شاشة المكافآت اليومية."""
        if self.manager.has_screen('daily_rewards'):
            self.manager.current = 'daily_rewards'

class GameScreen(Screen):
    display_clicks = NumericProperty(0)
    display_time = NumericProperty(TIME_LIMIT)
    display_best = NumericProperty(0)
    display_mode_title = StringProperty("CLASSIC MODE")
    background_color = ListProperty([0, 0, 0, 1])
    tap_button = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(GameScreen, self).__init__(**kwargs)
        self.game_mode = 'classic'
        self.reset_game_vars()
        
    def on_kv_post(self, base_widget):
        # ربط ids بعد تحميل KV
        self.tap_button = self.ids.tap_button
        
    def set_mode(self, mode):
        self.game_mode = mode
        if mode == 'classic':
            self.display_mode_title = "CLASSIC MODE"
        elif mode == 'survival':
            self.display_mode_title = "SURVIVAL MODE"
        elif mode == 'accuracy':
            self.display_mode_title = "ACCURACY MODE"
        elif mode == 'reaction':
            self.display_mode_title = "REACTION MODE"
            
    def reset_game_vars(self):
        self.clicks = 0
        self.time_left = TIME_LIMIT
        self.game_running = False
        self.timer_event = None
        self.foe_event = None
        self.powerup_event = None
        self.reaction_event = None
        self.wrong_taps_count = 0
        self.click_multiplier = 1.0
        self.penalty_time = BASE_PENALTY_TIME
        self.current_reaction_color = ""
        self.reaction_time_start = 0

    def apply_upgrades(self):
        """تطبيق تأثير الترقيات المشتراة."""
        app = App.get_running_app()
        
        self.click_multiplier = 1.0
        self.penalty_time = BASE_PENALTY_TIME
        
        for item_data in SHOP_ITEMS:
            if item_data['type'] == 'upgrade':
                level = app.currency_data.get('upgrades', {}).get(item_data['id'], 0)
                if level > 0:
                    if 'multiplier_increase' in item_data['effect']:
                        self.click_multiplier += item_data['effect']['multiplier_increase'] * level
                    if 'penalty_reduction' in item_data['effect']:
                        self.penalty_time -= item_data['effect']['penalty_reduction'] * level
                        self.penalty_time = max(0.1, self.penalty_time) 
                        
    def on_enter(self, *args):
        app = App.get_running_app()
        self.apply_upgrades()
        
        current_theme = next((item for item in SHOP_ITEMS if item['id'] == app.current_theme), None)
        self.background_color = current_theme['color'] if current_theme else [0, 0, 0, 1]
        Window.clearcolor = self.background_color 
        self.reset_game()
        
    def reset_game(self):
        self.reset_game_vars()
        self.apply_upgrades()

        app = App.get_running_app()
        if self.game_mode == 'classic':
            self.display_time = TIME_LIMIT
            self.display_best = app.high_score
        elif self.game_mode == 'survival':
            self.display_time = SURVIVAL_START_TIME
            self.display_best = app.stats_data.get('survival_high_time', 0.0)
        elif self.game_mode == 'accuracy':
            self.display_time = 999 
            self.display_best = app.stats_data.get('accuracy_high_score', 0)
        elif self.game_mode == 'reaction':
            self.display_time = 999 
            self.display_best = app.stats_data.get('reaction_high_score', 0)

        self.display_clicks = 0
        
        # إلغاء أي جدول زمني سابق للتأكد من نظافة اللعبة
        if self.timer_event: self.timer_event.cancel()
        if self.foe_event: self.foe_event.cancel()
        if self.powerup_event: self.powerup_event.cancel()
        if self.reaction_event: self.reaction_event.cancel()

        self.ids.tap_button.text = "START GAME"
        self.ids.tap_button.background_color = (0.2, 0.6, 1, 1)
        self.ids.foe_button.opacity = 0
        self.ids.foe_button.disabled = True
        self.ids.power_button.opacity = 0 
        self.ids.power_button.disabled = True
        
        # إلغاء ربط جميع الدوال قبل إعادة الربط للتأكد من عدم تكرار الاستدعاء
        self.ids.tap_button.unbind(on_press=self.start_game_on_tap)
        self.ids.tap_button.unbind(on_press=self.on_correct_tap)
        self.ids.tap_button.unbind(on_press=self.on_reaction_tap)

        self.ids.tap_button.bind(on_press=self.start_game_on_tap)

    def start_game_on_tap(self, instance):
        self.ids.tap_button.unbind(on_press=self.start_game_on_tap)
        
        if self.game_mode == 'reaction':
            self.ids.tap_button.bind(on_press=self.on_reaction_tap)
        else:
            self.ids.tap_button.bind(on_press=self.on_correct_tap)
            
        self.start_game()

    def start_game(self):
        self.game_running = True
        self.ids.tap_button.text = "TAP!"
        self.ids.tap_button.background_color = (0.3, 0.8, 0.3, 1)
        
        if self.game_mode == 'reaction':
            self.ids.foe_button.opacity = 0
            self.ids.power_button.opacity = 0
            self.schedule_reaction_cycle()
            return

        if self.game_mode != 'accuracy':
            self.timer_event = Clock.schedule_interval(self.update_timer, 0.1)
        
        foe_delay = random.uniform(1, 3) 
        powerup_delay = random.uniform(8, 15)
        
        if self.game_mode in ['classic', 'survival']:
            self.foe_event = Clock.schedule_once(self.show_foe_button, foe_delay)
            
        if self.game_mode in ['classic', 'survival']: 
            self.powerup_event = Clock.schedule_once(self.show_powerup_button, powerup_delay)

    # --- منطق وضع رد الفعل ---
    
    def schedule_reaction_cycle(self):
        if not self.game_running: return
        
        color_name = random.choice(list(REACTION_COLORS.keys()))
        self.current_reaction_color = color_name
        
        self.ids.tap_button.background_color = REACTION_COLORS[color_name]
        self.ids.tap_button.text = f"TAP {color_name}"
        
        self.reaction_time_start = Clock.get_time()
        
        self.reaction_event = Clock.schedule_once(self.reaction_timeout, REACTION_TIME_WINDOW)

    def reaction_timeout(self):
        if self.game_running:
            self.end_game()
            
    def on_reaction_tap(self, instance):
        if not self.game_running: return
        
        tap_time = Clock.get_time()
        reaction_time = tap_time - self.reaction_time_start
        
        if self.reaction_event: self.reaction_event.cancel()

        if reaction_time <= REACTION_TIME_WINDOW and self.current_reaction_color:
            
            app = App.get_running_app()
            app.stats_data['total_clicks'] = app.stats_data.get('total_clicks', 0) + 1
            save_data(STATS_FILE, app.stats_data)
            
            self.clicks += 1
            self.display_clicks = self.clicks
            
            self.flash_screen(color=REACTION_COLORS[self.current_reaction_color], duration=0.05)
            
            Clock.schedule_once(lambda dt: self.schedule_reaction_cycle(), 0.1)
            
        else:
            app = App.get_running_app()
            app.stats_data['total_wrong_taps'] = app.stats_data.get('total_wrong_taps', 0) + 1
            save_data(STATS_FILE, app.stats_data)
            self.wrong_taps_count += 1
            self.end_game()


    # --- معالجة الأزرار (كلاسيك/بقاء/دقة) ---
    
    def on_correct_tap(self, instance):
        if not self.game_running: return
        
        app = App.get_running_app()
        app.stats_data['total_clicks'] = app.stats_data.get('total_clicks', 0) + 1
        save_data(STATS_FILE, app.stats_data)
        
        self.clicks += (1 * self.click_multiplier) 
        self.display_clicks = self.clicks
        
        self.flash_screen(color=[1, 1, 1, 1], duration=0.05)
        
        if self.game_mode == 'survival':
            self.time_left += SURVIVAL_TIME_BONUS
            self.update_labels()
            
        self.ids.tap_button.background_color = (0.5, 1, 0.5, 1)
        Clock.schedule_once(lambda dt: setattr(self.ids.tap_button, 'background_color', (0.3, 0.8, 0.3, 1)), 0.1)

    def on_wrong_tap(self, instance):
        if not self.game_running: return
        
        app = App.get_running_app()
        app.stats_data['total_wrong_taps'] = app.stats_data.get('total_wrong_taps', 0) + 1
        save_data(STATS_FILE, app.stats_data)
        
        self.shake_screen(duration=0.2, intensity=5) 
        self.flash_screen(color=[1, 0, 0, 1], duration=0.2)
        
        if self.game_mode == 'accuracy':
            self.end_game()
            return

        self.wrong_taps_count += 1
        self.time_left -= self.penalty_time
        self.update_timer(0)
        
        self.ids.timer_label.text += f" (-{self.penalty_time:.1f}s Penalty!)"
        Clock.schedule_once(lambda dt: self.update_labels(), 0.5)

        self.hide_foe_button()
        Clock.schedule_once(self.show_foe_button, random.uniform(1, 3))

    def on_powerup_tap(self, instance):
        if not self.game_running: return
        
        self.time_left += 2.0 
        self.update_timer(0)
        self.ids.timer_label.text += " (+2s TIME BONUS!)"
        Clock.schedule_once(lambda dt: self.update_labels(), 0.5)

        self.hide_powerup_button() 
        self.powerup_event = Clock.schedule_once(self.show_powerup_button, random.uniform(8, 15))

    # --- التأثيرات البصرية والاهتزاز ---
    
    def flash_screen(self, color, duration):
        Window.clearcolor = color
        Clock.schedule_once(lambda dt: self.restore_color(self.background_color), duration)

    def restore_color(self, original_color):
        app = App.get_running_app()
        current_theme = next((item for item in SHOP_ITEMS if item['id'] == app.current_theme), None)
        Window.clearcolor = current_theme['color'] if current_theme else (0, 0, 0, 1)
        
    def shake_screen(self, duration=0.1, intensity=5):
        original_x = Window.left
        original_y = Window.top
        
        anim = Animation(left=original_x + intensity, duration=duration/4) + \
               Animation(left=original_x - intensity, duration=duration/4) + \
               Animation(top=original_y + intensity, duration=duration/4) + \
               Animation(top=original_y - intensity, duration=duration/4) + \
               Animation(left=original_x, top=original_y, duration=0.01)
               
        anim.start(Window)

    # --- إدارة الأزرار والحركة العشوائية ---
    
    def show_foe_button(self, dt):
        if not self.game_running: return
        
        self.ids.foe_button.pos_hint = {'x': random.uniform(0.05, 0.65), 'y': random.uniform(0.05, 0.55)}
        
        self.ids.foe_button.opacity = 1
        self.ids.foe_button.disabled = False
        
        delay = random.uniform(0.5, 1.5)

        self.foe_event = Clock.schedule_once(self.hide_foe_button, delay)
    
    def hide_foe_button(self, dt=None):
        self.ids.foe_button.opacity = 0
        self.ids.foe_button.disabled = True
        if self.game_running and self.game_mode in ['classic', 'survival']:
            delay = random.uniform(1, 4)
            self.foe_event = Clock.schedule_once(self.show_foe_button, delay)
            
    def show_powerup_button(self, dt):
        if not self.game_running: return
        self.ids.power_button.pos_hint = {'x': random.uniform(0.1, 0.7), 'y': random.uniform(0.1, 0.5)}
        
        self.ids.power_button.opacity = 1
        self.ids.power_button.disabled = False
        self.powerup_event = Clock.schedule_once(self.hide_powerup_button, 1.5)
    
    def hide_powerup_button(self, dt=None):
        self.ids.power_button.opacity = 0
        self.ids.power_button.disabled = True
        if self.game_running and self.game_mode not in ['accuracy', 'reaction']:
            self.powerup_event = Clock.schedule_once(self.show_powerup_button, random.uniform(8, 15))


    # --- إدارة المؤقت والإنهاء ---

    def update_labels(self):
        if self.game_mode == 'survival':
             self.ids.timer_label.text = f"Time: {max(0, self.time_left):.2f}s"
        elif self.game_mode == 'reaction':
             self.ids.timer_label.text = f"Reaction Clicks"
        else:
             self.ids.timer_label.text = f"Time: {max(0, self.time_left):.1f}s"

    def update_timer(self, dt):
        if not self.game_running or self.game_mode in ['accuracy', 'reaction']: return

        self.time_left -= dt
        self.display_time = self.time_left
        
        if self.time_left <= 0:
            self.time_left = 0
            self.end_game()
        
        self.update_labels()

    def end_game(self):
        app = App.get_running_app()

        # تحديث إجمالي الألعاب قبل إنهاء اللعبة
        app.stats_data['total_games_played'] = app.stats_data.get('total_games_played', 0) + 1 

        self.game_running = False
        if self.timer_event: self.timer_event.cancel()
        if self.foe_event: self.foe_event.cancel()
        if self.powerup_event: self.powerup_event.cancel()
        if self.reaction_event: self.reaction_event.cancel()
        
        self.ids.tap_button.text = "Game Over"
        self.ids.tap_button.background_color = (0.5, 0.5, 0.5, 1)
        self.ids.foe_button.opacity = 0
        self.ids.power_button.opacity = 0 
        
        coins_gained = 0
        if self.game_mode in ['classic', 'survival', 'reaction']:
            coins_gained = int(self.clicks * COINS_PER_CLICK * self.click_multiplier)
            app.currency_data['coins'] += coins_gained
            save_data(CURRENCY_FILE, app.currency_data)
        
        is_new_high_score = self.process_stats_and_achievements()
        
        results_screen = self.manager.get_screen('results')
        
        if self.game_mode == 'survival':
            final_score_display = self.time_left
        elif self.game_mode == 'reaction':
            final_score_display = self.clicks
        else:
            final_score_display = self.clicks
            
        results_screen.display_results(final_score_display, coins_gained, is_new_high_score, self.game_mode)
        self.manager.current = 'results'

    def process_stats_and_achievements(self):
        app = App.get_running_app()
        app.game_data["total_games"] = app.game_data.get("total_games", 0) + 1
        ach = app.game_data.get("achievements", {})
        
        # تحديث الإنجازات
        if self.clicks >= ACHIEVEMENTS_DATA["speed_demon"]["target"] and not ach.get("speed_demon", {}).get("unlocked", False):
            ach["speed_demon"] = {"unlocked": True}
            
        if self.wrong_taps_count == 0 and self.clicks > 0 and not ach.get("focused", {}).get("unlocked", False):
            ach["focused"] = {"unlocked": True}
            
        if app.game_data["total_games"] >= ACHIEVEMENTS_DATA["veteran"]["target"] and not ach.get("veteran", {}).get("unlocked", False):
            ach["veteran"] = {"unlocked": True}
            
        app.game_data["achievements"] = ach
        save_data(ACHIEVEMENTS_FILE, app.game_data)
        
        # تحديث أفضل النتائج والإحصائيات
        is_new_high_score = False
        if self.game_mode == 'classic' and self.clicks > app.high_score:
            app.high_score = self.clicks
            save_data(SCORE_FILE, {"high_score": app.high_score})
            is_new_high_score = True
        elif self.game_mode == 'survival' and self.time_left > app.stats_data.get('survival_high_time', 0.0):
             app.stats_data['survival_high_time'] = self.time_left
             is_new_high_score = True
        elif self.game_mode == 'accuracy' and self.clicks > app.stats_data.get('accuracy_high_score', 0):
             app.stats_data['accuracy_high_score'] = self.clicks
             is_new_high_score = True
        elif self.game_mode == 'reaction' and self.clicks > app.stats_data.get('reaction_high_score', 0):
             app.stats_data['reaction_high_score'] = self.clicks
             is_new_high_score = True
             
        save_data(STATS_FILE, app.stats_data)
        
        return is_new_high_score


class ResultsScreen(Screen):
    display_message = StringProperty("Game Over!")
    display_final_score = StringProperty("Score: 0")
    display_coins_gained = StringProperty("Coins Earned: 0")
    
    def display_results(self, final_score, coins_gained, is_new_high_score, mode):
        # تم التأكد من عدم استدعاء أي دالة صوتية هنا
        app = App.get_running_app()
        
        self.display_coins_gained = f"Coins Earned: {coins_gained} | Total: {app.currency_data['coins']}"
        
        if mode == 'classic':
            self.display_final_score = f"Your Score: {final_score}\nClassic Best: {app.high_score}"
            self.display_message = "NEW HIGH SCORE!" if is_new_high_score else "Time's Up!"
        elif mode == 'survival':
            self.display_final_score = f"Time Survived: {final_score:.2f}s\nSurvival Best: {app.stats_data['survival_high_time']:.2f}s"
            self.display_message = "New Survival Record!" if is_new_high_score else "Time's Up!"
        elif mode == 'accuracy':
            self.display_final_score = f"Clicks: {final_score}\nAccuracy Best: {app.stats_data['accuracy_high_score']}"
            self.display_message = "New Accuracy Record!" if is_new_high_score else "FAILED!"
        elif mode == 'reaction':
            self.display_final_score = f"Clicks: {final_score}\nReaction Best: {app.stats_data['reaction_high_score']}"
            self.display_message = "New Reaction Record!" if is_new_high_score else "FAILED!"


class ShopScreen(Screen):
    
    def on_enter(self, *args):
        app = App.get_running_app()
        self.ids.coins_label.text = f"Your Coins: {app.currency_data['coins']}"
        self.ids.shop_container.clear_widgets()
        
        shop_container = self.ids.shop_container
        
        for item in SHOP_ITEMS:
            # حساب الحالة والسعر والمستوى للعرض
            status = ""
            current_level = app.currency_data.get('upgrades', {}).get(item['id'], 0)
            
            if item['type'] == 'upgrade':
                max_level = item.get('max_level', 1)
                actual_price = item['price'] * (current_level + 1)
                
                if current_level >= max_level:
                    status = "MAX"
                    display_price = 0
                else:
                    status = f"LV {current_level} -> {current_level + 1}"
                    display_price = actual_price
            
            elif item['type'] == 'theme':
                is_unlocked = item['id'] in app.currency_data.get('unlocked_themes', [])
                if is_unlocked:
                    status = "EQUIP" if item['id'] != app.current_theme else "ACTIVE"
                    display_price = 0
                else:
                    status = "UNLOCK"
                    display_price = item['price']

            # استخدام Factory.ShopItem لإنشاء العنصر المخصص
            shop_container.add_widget(Factory.ShopItem(
                item_id=item['id'],
                item_name=item['name'],
                item_price=display_price, 
                item_color=item.get('color', [0.2, 0.2, 0.2, 1]),
                item_type=item['type'],
                display_status=status
            ))


    def purchase_or_activate(self, item_id, price, item_type):
        app = App.get_running_app()
        
        item = next(item for item in SHOP_ITEMS if item['id'] == item_id)
        
        if item_type == 'upgrade':
            current_level = app.currency_data.get('upgrades', {}).get(item_id, 0)
            max_level = item.get('max_level', 1)
            
            if current_level >= max_level:
                self.ids.status_label.text = "Max Level Reached!"
                return
            
            actual_price = item['price'] * (current_level + 1)
            
            if actual_price > app.currency_data['coins']:
                self.ids.status_label.text = "Not enough coins!"
                return
            
            app.currency_data['coins'] -= actual_price
            app.currency_data['upgrades'][item_id] = current_level + 1
            save_data(CURRENCY_FILE, app.currency_data)
            self.ids.status_label.text = f"{item['name']} Upgraded to Lv. {current_level + 1}!"
        
        elif item_type == 'theme':
            is_unlocked = item_id in app.currency_data.get('unlocked_themes', [])
            
            if is_unlocked:
                self.select_theme(item_id)
                return
                
            if price > app.currency_data['coins']:
                self.ids.status_label.text = "Not enough coins!"
                return
                
            app.currency_data['coins'] -= price
            # التأكد من وجود القائمة قبل الإضافة
            if 'unlocked_themes' not in app.currency_data:
                 app.currency_data['unlocked_themes'] = []
            app.currency_data['unlocked_themes'].append(item_id)
            save_data(CURRENCY_FILE, app.currency_data)
            self.ids.status_label.text = f"{item['name']} Unlocked!"
            self.select_theme(item_id)
            
        self.on_enter()


    def select_theme(self, theme_id):
        app = App.get_running_app()
        app.current_theme = theme_id
        current_theme_data = next((item for item in SHOP_ITEMS if item['id'] == theme_id), None)
        if current_theme_data:
             Window.clearcolor = current_theme_data['color']
        
        self.ids.status_label.text = f"{theme_id.replace('bg_', '').capitalize()} Theme Activated!"

class ModeSelectScreen(Screen):
    pass

class StatsScreen(Screen):
    total_clicks = NumericProperty(0)
    total_wrong_taps = NumericProperty(0)
    total_games_played = NumericProperty(0)
    survival_high_time = StringProperty("0.00s")
    accuracy_high_score = NumericProperty(0)
    reaction_high_score = NumericProperty(0)
    
    def on_enter(self, *args):
        app = App.get_running_app()
        stats = app.stats_data
        
        self.total_clicks = stats.get('total_clicks', 0)
        self.total_wrong_taps = stats.get('total_wrong_taps', 0)
        self.total_games_played = stats.get('total_games_played', 0)
        self.survival_high_time = f"{stats.get('survival_high_time', 0.0):.2f}s"
        self.accuracy_high_score = stats.get('accuracy_high_score', 0)
        self.reaction_high_score = stats.get('reaction_high_score', 0)

# --- شاشة المكافآت اليومية (Daily Rewards) ---
class DailyRewardsScreen(Screen):
    # عرض معلومات الواجهة
    title_text = StringProperty("Daily Rewards")
    streak_text = StringProperty("")  # يعرض "Day X of 7"
    rewards_preview = StringProperty("")  # نص يوضح مكافآت الأيام
    collect_enabled = BooleanProperty(False)
    collect_message = StringProperty("")  # رسالة حالة (تم جمعه، جاهز، الخ)
    today_reward_text = StringProperty("")  # يعرض قيمة مكافأة اليوم
    
    def on_enter(self, *args):
        # تحميل بيانات الحالة وتحديث الواجهة
        app = App.get_running_app()
        if "daily_reward" not in app.currency_data:
            app.currency_data["daily_reward"] = {"last_claim": "", "streak_day": 0, "last_claim_date": ""}
            save_data(CURRENCY_FILE, app.currency_data)

        self.refresh_view()

    def refresh_view(self):
        """تحديث بيانات الشاشة (حالة الستريك، مكافآت الأيام، تمكين زر الجمع)."""
        app = App.get_running_app()
        daily = app.currency_data.get("daily_reward", {"last_claim": "", "streak_day": 0, "last_claim_date": ""})
        last_claim_date = daily.get("last_claim_date", "")
        streak_day = daily.get("streak_day", 0)

        today_iso = date.today().isoformat()
        yesterday_iso = (date.today() - timedelta(days=1)).isoformat()

        next_day_number = min(streak_day + 1, 7)

        # تجهيز نص المكافآت لعرض سريع
        rewards_lines = []
        for idx, amt in enumerate(DAILY_STREAK_REWARDS, start=1):
            prefix = "•"
            if idx == next_day_number:
                prefix = "→"  # يبرز اليوم التالي
            if idx == 7:
                rewards_lines.append(f"{prefix} Day {idx}: {amt} Coins + Premium Theme")
            else:
                rewards_lines.append(f"{prefix} Day {idx}: {amt} Coins")
        self.rewards_preview = "\n".join(rewards_lines)

        # ضبط نص الستريك
        self.streak_text = f"Current Streak Day: {streak_day} / 7"

        # هل يمكن جمع مكافأة اليوم؟
        if last_claim_date != today_iso:
            self.collect_enabled = True
            self.collect_message = f"Collect your Day {next_day_number} reward!"
            self.today_reward_text = f"Today's Reward: {DAILY_STREAK_REWARDS[next_day_number-1]} Coins"
        else:
            self.collect_enabled = False
            self.collect_message = "You've already collected today's reward."
            self.today_reward_text = f"Today's Reward: Collected ({DAILY_STREAK_REWARDS[max(0, min(streak_day,7)-1)]} Coins)"

    def collect_reward(self):
        """تنفيذ عملية جمع المكافأة عند الضغط على زر Collect"""
        app = App.get_running_app()
        daily = app.currency_data.get("daily_reward", {"last_claim": "", "streak_day": 0, "last_claim_date": ""})
        last_claim_date = daily.get("last_claim_date", "")
        streak_day = daily.get("streak_day", 0)

        today_iso = date.today().isoformat()
        yesterday_iso = (date.today() - timedelta(days=1)).isoformat()

        # إذا جمعت اليوم بالفعل: لا تعمل
        if last_claim_date == today_iso:
            self.collect_message = "Already collected today."
            self.collect_enabled = False
            return

        # إذا جمع المستخدم البارحة، نزيد الستريك، وإلا نعيده إلى 1
        if last_claim_date == yesterday_iso:
            new_streak = min(streak_day + 1, 7)
        else:
            new_streak = 1

        reward_idx = new_streak - 1
        reward_amount = DAILY_STREAK_REWARDS[reward_idx]

        # منح العملات
        app.currency_data['coins'] = app.currency_data.get('coins', 0) + reward_amount
        # تحديث بيانات الستريك وتاريخ آخر جمع
        app.currency_data['daily_reward']['streak_day'] = new_streak
        app.currency_data['daily_reward']['last_claim_date'] = today_iso

        # إذا كان اليوم السابع: فتح ثيم بريميوم إن لم يكن مفتوحًا
        if new_streak >= 7:
            if 'unlocked_themes' not in app.currency_data:
                app.currency_data['unlocked_themes'] = []
            if 'bg_premium' not in app.currency_data['unlocked_themes']:
                app.currency_data['unlocked_themes'].append('bg_premium')
                # اجعل الثيم مفعلًا بشكل افتراضي بعد فتحه (اختياري)
                app.current_theme = 'bg_premium'
                # تحديث نافذة الحالة (إن وجدت)
                # (لا نعرض رسالة مودال هنا — نكتفي بتحديث status)
        
        save_data(CURRENCY_FILE, app.currency_data)

        # تحديث واجهة الشاشة والعودة إلى القائمة أو إبقاء المستخدم هنا
        self.collect_message = f"Collected {reward_amount} Coins! (Streak: {new_streak}/7)"
        self.collect_enabled = False
        self.streak_text = f"Current Streak Day: {new_streak} / 7"
        # تحديث عرض العملات على شاشة القائمة إن كانت ظاهرة
        if self.manager.has_screen('menu'):
            menu = self.manager.get_screen('menu')
            menu.display_coins = f"Coins: {app.currency_data.get('coins', 0)}"
            menu.check_daily_status()

class ClickerApp(App):
    high_score = NumericProperty(0)
    game_data = DictProperty({})
    currency_data = DictProperty({})
    stats_data = DictProperty({})
    current_theme = StringProperty("default")

    def build(self):
        self.high_score = load_data(SCORE_FILE, {"high_score": 0}).get("high_score", 0)
        self.game_data = load_data(ACHIEVEMENTS_FILE, {"total_games": 0, "achievements": {}})
        self.currency_data = load_data(CURRENCY_FILE, {"coins": 0, "unlocked_themes": ["default"], "upgrades": {}, "daily_reward": {"last_claim": "", "streak_day": 0, "last_claim_date": ""}})
        self.stats_data = load_data(STATS_FILE, DEFAULT_STATS)
        
        if not self.current_theme or self.current_theme not in self.currency_data.get('unlocked_themes', []):
             self.current_theme = "default"
        
        current_theme_data = next((item for item in SHOP_ITEMS if item['id'] == self.current_theme), None)
        Window.clearcolor = current_theme_data['color'] if current_theme_data else (0, 0, 0, 1)
        
        # تحميل ملف الواجهة (game_design.kv) - تأكد أن الـ KV يحتوي شاشة 'daily_rewards'
        return Builder.load_file('game_design.kv')

if __name__ == '__main__':
    ClickerApp().run()