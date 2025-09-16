# filepath: c:\Users\Maoer\Desktop\AstrBotLauncher-0.1.5.6\AstrBot\data\plugins\steam_status_monitor_V2\game_end_render.py
import os
import io
import time
import asyncio
import httpx
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# 更深的蓝紫色到黑色渐变
BG_COLOR_TOP = (24, 18, 48)   # 顶部深蓝紫
BG_COLOR_BOTTOM = (8, 8, 16)  # 底部接近黑色
AVATAR_SIZE = 80
COVER_W, COVER_H = 80, 120
IMG_W, IMG_H = 512, 192

# 星星素材路径（假定与本文件同目录）
STAR_BG_PATH = os.path.join(os.path.dirname(__file__), "随机散布的小星星767x809xp.png")

SGDB_API_KEY = "00c703ea9a664ce236526aca0faeaaf4"

async def get_sgdb_vertical_cover(game_name, sgdb_api_key=None):
    if not sgdb_api_key:
        return None
    headers = {"Authorization": f"Bearer {sgdb_api_key}"}
    search_url = f"https://www.steamgriddb.com/api/v2/search/autocomplete/{game_name}"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(search_url, headers=headers)
            data = resp.json()
            if not data.get("success") or not data.get("data"):
                return None
            sgdb_game_id = data["data"][0]["id"]
            grid_url = f"https://www.steamgriddb.com/api/v2/grids/game/{sgdb_game_id}?dimensions=600x900&type=static&limit=1"
            resp2 = await client.get(grid_url, headers=headers)
            data2 = resp2.json()
            if not data2.get("success") or not data2.get("data"):
                return None
            return data2["data"][0]["url"]
        except Exception as e:
            print(f"[get_sgdb_vertical_cover] SGDB API异常: {e}")
            return None

def get_avatar_path(data_dir, steamid, url, force_update=False):
    avatar_dir = os.path.join(data_dir, "avatars")
    os.makedirs(avatar_dir, exist_ok=True)
    path = os.path.join(avatar_dir, f"{steamid}.jpg")
    refresh_interval = 24 * 3600
    print(f"[game_end_render] get_avatar_path: url={url}, path={path}, exists={os.path.exists(path)}")
    if os.path.exists(path) and not force_update:
        if time.time() - os.path.getmtime(path) < refresh_interval:
            print(f"[game_end_render] 使用本地头像: {path}, size={os.path.getsize(path)}")
            return path
    try:
        import httpx
        resp = httpx.get(url, timeout=10)
        if resp.status_code == 200:
            with open(path, "wb") as f:
                f.write(resp.content)
            print(f"[game_end_render] 下载头像成功: {path}, size={os.path.getsize(path)}")
            return path
        else:
            print(f"[game_end_render] 头像下载失败: HTTP {resp.status_code} url={url}")
    except Exception as e:
        import traceback
        print(f"[game_end_render] 头像下载异常: {e}\n{traceback.format_exc()}")
    return path if os.path.exists(path) else None

# 渐变背景函数补充
def render_gradient_bg(img_w, img_h, color_top, color_bottom):
    base = Image.new("RGB", (img_w, img_h), color_top)
    top_r, top_g, top_b = color_top
    bot_r, bot_g, bot_b = color_bottom
    for y in range(img_h):
        ratio = y / (img_h - 1)
        r = int(top_r * (1 - ratio) + bot_r * ratio)
        g = int(top_g * (1 - ratio) + bot_g * ratio)
        b = int(top_b * (1 - ratio) + bot_b * ratio)
        for x in range(img_w):
            base.putpixel((x, y), (r, g, b))
    return base

# get_cover_path 改为 async def 并 await get_sgdb_vertical_cover
async def get_cover_path(data_dir, gameid, game_name, force_update=False, sgdb_api_key=None):
    from PIL import Image as PILImage
    from io import BytesIO
    import httpx
    cover_dir = os.path.join(data_dir, "covers_v")
    os.makedirs(cover_dir, exist_ok=True)
    path = os.path.join(cover_dir, f"{gameid}.jpg")
    # 只在本地不存在时才云端获取
    if os.path.exists(path):
        return path
    # 1. SGDB优先
    url = await get_sgdb_vertical_cover(game_name, sgdb_api_key)
    if url:
        try:
            resp = httpx.get(url, timeout=10)
            if resp.status_code == 200:
                with open(path, "wb") as f:
                    f.write(resp.content)
                return path
        except Exception as e:
            print(f"[get_cover_path] SGDB下载异常: {e} url={url}")
    # 2. fallback: 官方 capsule_600x900（竖版）优先，其次 header_image（横版）
    try:
        store_url = f"https://store.steampowered.com/api/appdetails?appids={gameid}&l=schinese"
        resp = httpx.get(store_url, timeout=10)
        data = resp.json()
        info = data.get(str(gameid), {}).get("data", {})
        # 先尝试 capsule_600x900
        capsule_img = info.get("capsule_image")
        if not capsule_img:
            # 兼容部分API未返回 capsule_image 字段
            header_img = info.get("header_image")
            if header_img:
                capsule_img = header_img.replace("_header.jpg", "_capsule_600x900.jpg")
        if capsule_img:
            img_resp = httpx.get(capsule_img, timeout=10)
            if img_resp.status_code == 200:
                img = PILImage.open(BytesIO(img_resp.content)).convert("RGB")
                # 只缩放高度为900，宽度等比例缩放
                scale = 900 / img.height
                new_w = int(img.width * scale)
                new_h = 900
                img = img.resize((new_w, new_h), PILImage.LANCZOS)
                img.save(path)
                return path
        # fallback: header_image 横版
        header_img = info.get("header_image")
        if header_img:
            img_resp = httpx.get(header_img, timeout=10)
            if img_resp.status_code == 200:
                img = PILImage.open(BytesIO(img_resp.content)).convert("RGB")
                # 只缩放高度为900，宽度等比例缩放
                scale = 900 / img.height
                new_w = int(img.width * scale)
                new_h = 900
                img = img.resize((new_w, new_h), PILImage.LANCZOS)
                img.save(path)
                return path
    except Exception as e:
        print(f"[get_cover_path] fallback capsule/header_image异常: {e}")
    print(f"[get_cover_path] 封面获取失败: {gameid} {game_name}")
    return path if os.path.exists(path) else None

def draw_duration_bar(draw, x, y, width, height, duration_h):
    pad = 1
    # 先画底色和描边
    draw.rounded_rectangle([x-pad, y-pad, x+width+pad, y+height+pad], radius=(height+pad)//2, fill=(0,0,0,180))
    draw.rounded_rectangle([x, y, x + width, y + height], radius=height//2, outline=(0,0,0,255), width=1)
    draw.rounded_rectangle([x-2, y-2, x + width+2, y + height+2], radius=(height+4)//2, outline=(255,255,255,220), width=1)
    bar_colors = [
        (80, 200, 120),    # 1小时 绿色
        (255, 220, 80),    # 3小时 黄色
        (255, 160, 80),    # 5小时 橙色
        (255, 80, 80),     # 7小时 红色
        (200, 80, 160),    # 9小时 紫红色
        (120, 80, 200)     # 12小时 深紫色
    ]
    seg_limits = [1, 3, 5, 7, 9, 12]
    seg_starts = [0] + seg_limits[:-1]
    seg_texts = [None, "2X", "3X", "4X", "5X", "6X"]
    if duration_h > 12:
        # 彩色渐变条
        for i in range(width):
            ratio = i / max(width-1, 1)
            # 渐变色：红橙黄绿青蓝紫
            from colorsys import hsv_to_rgb
            rgb = hsv_to_rgb(ratio, 0.8, 1.0)
            color = tuple(int(c*255) for c in rgb)
            draw.line([(x+i, y), (x+i, y+height)], fill=color, width=1)
        # 叠加MAX文字
        try:
            font = ImageFont.truetype("msyhbd.ttc", height+8)
        except:
            font = ImageFont.load_default()
        text = "MAX"
        text_bbox = draw.textbbox((0,0), text, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]
        center_x = x + width // 2 - text_w // 2
        center_y = y + height // 2 - text_h // 2 - 5
        draw.text((center_x, center_y), text, font=font, fill=(255,255,255,255), stroke_width=2, stroke_fill=(0,0,0,180))
    else:
        # 普通分段条
        for i, (seg_start, seg_end, color) in enumerate(zip(seg_starts, seg_limits, bar_colors)):
            seg_val = min(max(duration_h - seg_start, 0), seg_end - seg_start)
            seg_ratio = seg_val / (seg_end - seg_start) if seg_end > seg_start else 0
            seg_w = int(width * seg_ratio)
            if seg_w > 0:
                draw.rounded_rectangle([x, y, x + seg_w, y + height], radius=height//2, fill=color)
        for i, (seg_start, seg_end, color) in enumerate(zip(seg_starts, seg_limits, bar_colors)):
            if seg_texts[i] and duration_h > seg_start:
                text = seg_texts[i]
                try:
                    font = ImageFont.truetype("msyhbd.ttc", height+6)
                except:
                    font = ImageFont.load_default()
                text_bbox = draw.textbbox((0,0), text, font=font)
                text_w = text_bbox[2] - text_bbox[0]
                text_h = text_bbox[3] - text_bbox[1]
                center_x = x + width // 2 - text_w // 2
                center_y = y + height // 2 - text_h // 2 - 5
                draw.text((center_x, center_y), text, font=font, fill=color, stroke_width=2, stroke_fill=(0,0,0,180))

def render_game_end_image(player_name, avatar_path, game_name, cover_path, end_time_str, tip_text, duration_h):
    # 字体
    try:
        font_bold = ImageFont.truetype("msyhbd.ttc", 28)
        font = ImageFont.truetype("msyh.ttc", 22)
        font_small = ImageFont.truetype("msyh.ttc", 16)
        font_tip = ImageFont.truetype("msyh.ttc", 16)
    except:
        font_bold = font = font_small = font_tip = ImageFont.load_default()

    img = render_gradient_bg(IMG_W, IMG_H, BG_COLOR_TOP, BG_COLOR_BOTTOM).convert("RGBA")
    draw = ImageDraw.Draw(img)

    # 1. 背景星星横向平铺（等比例缩放高度，透明度30%）
    try:
        star_bg = Image.open(STAR_BG_PATH).convert("RGBA")
        star_w, star_h = star_bg.size
        scale = IMG_H / star_h
        new_w = int(star_w * scale)
        new_h = IMG_H
        star_bg_resized = star_bg.resize((new_w, new_h), Image.LANCZOS)
        # 设置透明度30%
        alpha = star_bg_resized.split()[-1].point(lambda p: int(p * 0.3))
        star_bg_resized.putalpha(alpha)
        for x in range(0, IMG_W, new_w):
            img.alpha_composite(star_bg_resized, (x, 0))
    except Exception as e:
        print(f"[game_end_render] 星星背景加载失败: {e}")

    # 2. 封面图左侧，等比例缩放高度，宽度自适应，不裁剪，左贴右留空
    cover_area_h = IMG_H
    new_w = COVER_W
    if cover_path and os.path.exists(cover_path):
        try:
            cover_src = Image.open(cover_path).convert("RGBA")
            scale = cover_area_h / cover_src.height
            new_w = int(cover_src.width * scale)
            new_h = cover_area_h
            cover_resized = cover_src.resize((new_w, new_h), Image.LANCZOS)
            # 修正：如果new_w大于画布宽度，限制最大宽度为画布宽度，防止超出
            if new_w > IMG_W:
                cover_resized = cover_resized.crop((0, 0, IMG_W, new_h))
                new_w = IMG_W
            img.paste(cover_resized, (0, 0), cover_resized)
        except Exception as e:
            print(f"[game_end_render] 封面加载失败: {e}")

    # 3. 头像（仅圆角，无柔光特效）
    avatar_x = new_w + 24
    avatar_y = 16
    if avatar_path and os.path.exists(avatar_path):
        try:
            print(f"[game_end_render] 尝试打开头像: {avatar_path}")
            avatar = Image.open(avatar_path).convert("RGBA").resize((AVATAR_SIZE, AVATAR_SIZE))
            # 圆角遮罩
            mask = Image.new("L", (AVATAR_SIZE, AVATAR_SIZE), 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.rounded_rectangle((0, 0, AVATAR_SIZE, AVATAR_SIZE), radius=AVATAR_SIZE//5, fill=255)
            avatar_rgba = avatar.copy()
            avatar_rgba.putalpha(mask)
            img.alpha_composite(avatar_rgba, (avatar_x, avatar_y))
        except Exception as e:
            import traceback
            print(f"[game_end_render] 头像加载失败: {e}\n{traceback.format_exc()}")

    # 今日人品（0~100），显示在头像正下方，字体更小，每个steamid每天固定
    import random, datetime, hashlib
    today = datetime.date.today().isoformat()
    luck_seed = f"{player_name}_{today}".encode("utf-8")
    today_luck = int(hashlib.md5(luck_seed).hexdigest(), 16) % 101
    luck_text = f"今日人品：{today_luck}"
    try:
        font_luck = ImageFont.truetype("msyh.ttc", 12)
    except:
        font_luck = ImageFont.load_default()
    luck_font_y = avatar_y + AVATAR_SIZE + 8
    draw.text((avatar_x, luck_font_y), luck_text, font=font_luck, fill=(200,220,255,220), stroke_width=1, stroke_fill=(0,0,0,255))

    # 当前时间叠加在最上方右上角，字号更小
    try:
        from datetime import datetime
        t = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M")
        time_str = t.strftime("%H:%M")
    except Exception:
        time_str = end_time_str[-5:]
    time_font_size = 8
    try:
        font_time = ImageFont.truetype("msyhbd.ttc", time_font_size)
    except:
        font_time = ImageFont.load_default()
    bbox = draw.textbbox((0,0), time_str, font=font_time, stroke_width=2)
    time_x = IMG_W - bbox[2] + bbox[0] - 18  # 右上角，留边距
    time_y = 6
    draw.text((time_x, time_y), time_str, font=font_time, fill=(255,255,255,220), stroke_width=2, stroke_fill=(0,0,0,255))

    # 4. 玩家名，顶部居左，自适应字号防止出界
    title_text = f"{player_name} 结束游戏"
    # 计算最大宽度（头像右侧到画布右侧，留24px边距）
    max_title_w = IMG_W - (avatar_x + AVATAR_SIZE + 20) - 24
    title_font_size = 28
    for size in range(28, 15, -2):
        try:
            font_title_tmp = ImageFont.truetype("msyhbd.ttc", size)
        except:
            font_title_tmp = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), title_text, font=font_title_tmp)
        if bbox[2] - bbox[0] <= max_title_w:
            title_font_size = size
            break
    try:
        font_title = ImageFont.truetype("msyhbd.ttc", title_font_size)
    except:
        font_title = ImageFont.load_default()
    draw.text((avatar_x + AVATAR_SIZE + 20, 16), title_text, font=font_title, fill=(180,160,255,255), stroke_width=2, stroke_fill=(0,0,0,255))

    # 5. 游戏名，头像右侧居左，第二行
    try:
        font_game = ImageFont.truetype("msyh.ttc", 22)
    except:
        font_game = font_title
    game_name_y = 16 + font_title.size + 8
    draw.text((avatar_x + AVATAR_SIZE + 20, game_name_y), game_name, font=font_game, fill=(220,220,255,255), stroke_width=2, stroke_fill=(0,0,0,255))

    # 6. 空几行（间隔）
    tip_y = game_name_y + font_game.size + 28

    # 7. 进度条和时长文本，放在头像列的底部，与今日人品同列
    bar_x = avatar_x
    bar_y = IMG_H - 24
    if duration_h < 1:
        min_text = f"已玩{int(duration_h*60)}分钟："
    else:
        min_text = f"已玩{duration_h:.1f}小时："
    # 文字略抬高，进度条略降低
    draw.text((bar_x, bar_y-2), min_text, font=font_tip, fill=(180, 220, 255, 220), stroke_width=1, stroke_fill=(0,0,0,255))
    min_text_bbox = draw.textbbox((bar_x, bar_y-2), min_text, font=font_tip)
    bar_start_x = min_text_bbox[2] + 6
    bar_w = IMG_W - bar_start_x - 18  # 进度条延伸到画布结尾，右侧留18px
    bar_h = 6
    draw_duration_bar(draw, bar_start_x, bar_y+6, bar_w, bar_h, duration_h)

    # 8. 友好提示词，玩家名列底部，且与进度条有间隔
    tip_y = bar_y - font_tip.size - 8
    draw.text((bar_x, tip_y), tip_text, font=font_tip, fill=(200,180,255,200), stroke_width=1, stroke_fill=(0,0,0,255))
    return img.convert("RGB")

# render_game_end 里 await get_cover_path
async def render_game_end(data_dir, steamid, player_name, avatar_url, gameid, game_name, end_time_str, tip_text, duration_h, sgdb_api_key=None):
    avatar_path = get_avatar_path(data_dir, steamid, avatar_url)
    cover_path = await get_cover_path(data_dir, gameid, game_name, sgdb_api_key=sgdb_api_key)
    img = render_game_end_image(player_name, avatar_path, game_name, cover_path, end_time_str, tip_text, duration_h)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()
