# -*- coding: utf-8 -*-
import re
from datetime import datetime
import time

from playwright.async_api import Playwright, async_playwright
import os
import asyncio

from conf import LOCAL_CHROME_PATH
from uploader.tk_uploader.tk_config import Tk_Locator
from utils.base_social_media import set_init_script
from utils.files_times import get_absolute_path
from utils.log import tiktok_logger


async def cookie_auth(account_file):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://www.tiktok.com/tiktokstudio/upload?lang=en")
        await page.wait_for_load_state('networkidle')
        try:
            # 选择所有的 select 元素
            select_elements = await page.query_selector_all('select')
            for element in select_elements:
                class_name = await element.get_attribute('class')
                # 使用正则表达式匹配特定模式的 class 名称
                if re.match(r'tiktok-.*-SelectFormContainer.*', class_name):
                    tiktok_logger.error("[+] cookie expired")
                    return False
            tiktok_logger.success("[+] cookie valid")
            return True
        except:
            tiktok_logger.success("[+] cookie valid")
            return True


async def tiktok_setup(account_file, handle=False):
    account_file = get_absolute_path(account_file, "tk_uploader")
    if not os.path.exists(account_file) or not await cookie_auth(account_file):
        if not handle:
            return False
        tiktok_logger.info('[+] cookie file is not existed or expired. Now open the browser auto. Please login with your way(gmail phone, whatever, the cookie file will generated after login')
        await get_tiktok_cookie(account_file)
    return True


async def get_tiktok_cookie(account_file):
    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB',
            ],
            'headless': False,  # Set headless option here
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # Pause the page, and start recording manually.
        page = await context.new_page()
        await page.goto("https://www.tiktok.com/login?lang=en")
        await page.pause()
        # 点击调试器的继续，保存cookie
        await context.storage_state(path=account_file)


class TiktokVideo(object):
    def __init__(self, title, file_path, tags, publish_date, account_file, thumbnail_path=None):
        self.title = title
        self.file_path = file_path
        self.tags = tags
        self.publish_date = publish_date
        self.thumbnail_path = thumbnail_path
        self.account_file = account_file
        self.local_executable_path = LOCAL_CHROME_PATH
        self.locator_base = None

    async def set_schedule_time(self, page, publish_date):
        schedule_input_element = self.locator_base.get_by_label('Schedule')
        await schedule_input_element.wait_for(state='visible')  # 确保按钮可见

        await schedule_input_element.click(force=True)
        if await self.locator_base.locator('div.TUXButton-content >> text=Allow').count():
            await self.locator_base.locator('div.TUXButton-content >> text=Allow').click()

        scheduled_picker = self.locator_base.locator('div.scheduled-picker')
        await scheduled_picker.locator('div.TUXInputBox').nth(1).click()

        calendar_month = await self.locator_base.locator(
            'div.calendar-wrapper span.month-title').inner_text()

        n_calendar_month = datetime.strptime(calendar_month, '%B').month

        schedule_month = publish_date.month

        if n_calendar_month != schedule_month:
            if n_calendar_month < schedule_month:
                arrow = self.locator_base.locator('div.calendar-wrapper span.arrow').nth(-1)
            else:
                arrow = self.locator_base.locator('div.calendar-wrapper span.arrow').nth(0)
            await arrow.click()

        # day set
        valid_days_locator = self.locator_base.locator(
            'div.calendar-wrapper span.day.valid')
        valid_days = await valid_days_locator.count()
        for i in range(valid_days):
            day_element = valid_days_locator.nth(i)
            text = await day_element.inner_text()
            if text.strip() == str(publish_date.day):
                await day_element.click()
                break
        # time set
        await scheduled_picker.locator('div.TUXInputBox').nth(0).click()

        hour_str = publish_date.strftime("%H")
        correct_minute = int(publish_date.minute / 5)
        minute_str = f"{correct_minute:02d}"

        hour_selector = f"span.tiktok-timepicker-left:has-text('{hour_str}')"
        minute_selector = f"span.tiktok-timepicker-right:has-text('{minute_str}')"

        # pick hour first
        await page.wait_for_timeout(1000)  # 等待500毫秒
        await self.locator_base.locator(hour_selector).click()
        # click time button again
        await page.wait_for_timeout(1000)  # 等待500毫秒
        # pick minutes after
        await self.locator_base.locator(minute_selector).click()

        # click title to remove the focus.
        # await self.locator_base.locator("h1:has-text('Upload video')").click()

    async def handle_upload_error(self, page):
        tiktok_logger.info("video upload error retrying.")
        select_file_button = self.locator_base.locator('button[aria-label="Select file"]')
        async with page.expect_file_chooser() as fc_info:
            await select_file_button.click()
        file_chooser = await fc_info.value
        await file_chooser.set_files(self.file_path)

    async def upload(self, playwright: Playwright) -> None:
        # Guard executable_path: only use if non-empty, exists and is executable; otherwise fallback.
        launch_kwargs = {"headless": False}
        path = (self.local_executable_path or "").strip()
        try:
            if path and os.path.isfile(path) and os.access(path, os.X_OK):
                launch_kwargs["executable_path"] = path
            else:
                # Fallback to Playwright-managed browser or system Chrome channel
                # Avoid passing an invalid path like '' which results in spawn . EACCES
                tiktok_logger.info("[browser] LOCAL_CHROME_PATH 未设置或不可执行，使用默认浏览器/Chrome 渠道")
                # Uncomment next line if you prefer system Chrome over bundled Chromium
                # launch_kwargs["channel"] = "chrome"
        except Exception:
            # Any unexpected error falls back to default
            tiktok_logger.info("[browser] 解析浏览器路径失败，回退到默认设置")

        browser = await playwright.chromium.launch(**launch_kwargs)
        context = await browser.new_context(storage_state=f"{self.account_file}")
        # context = await set_init_script(context)
        page = await context.new_page()

        # change language to eng first
        await self.change_language(page)
        await page.goto("https://www.tiktok.com/tiktokstudio/upload")
        tiktok_logger.info(f'[+]Uploading-------{self.title}.mp4')

        await page.wait_for_url("https://www.tiktok.com/tiktokstudio/upload", timeout=10000)

        try:
            await page.wait_for_selector('iframe[data-tt="Upload_index_iframe"], div.upload-container', timeout=10000)
            tiktok_logger.info("Either iframe or div appeared.")
        except Exception as e:
            tiktok_logger.error("Neither iframe nor div appeared within the timeout.")

        await self.choose_base_locator(page)

        upload_button = self.locator_base.locator(
            'button:has-text("Select video"):visible')
        await upload_button.wait_for(state='visible')  # 确保按钮可见

        async with page.expect_file_chooser() as fc_info:
            await upload_button.click()
        file_chooser = await fc_info.value
        await file_chooser.set_files(self.file_path)

        await self.add_title_tags(page)
        # detect upload status
        await self.detect_upload_status(page)
        if self.thumbnail_path:
            tiktok_logger.info(f'[+] Uploading thumbnail file {self.title}.png')
            await self.upload_thumbnails(page)

        if self.publish_date != 0:
            await self.set_schedule_time(page, self.publish_date)

        await self.click_publish(page)
        tiktok_logger.success(f"video_id: {await self.get_last_video_id(page)}")

        await context.storage_state(path=f"{self.account_file}")  # save cookie
        tiktok_logger.info('  [-] update cookie！')
        await asyncio.sleep(2)  # close delay for look the video status
        # close all
        await context.close()
        await browser.close()

    async def add_title_tags(self, page):
        await self.ensure_modal_closed(page, wait_seconds=5)
        editor_locator = self.locator_base.locator('div.public-DraftEditor-content')
        await editor_locator.click()

        await page.keyboard.press("End")

        await page.keyboard.press("Control+A")

        await page.keyboard.press("Delete")

        await page.keyboard.press("End")

        await page.wait_for_timeout(1000)  # 等待1秒

        await page.keyboard.insert_text(self.title)
        await page.wait_for_timeout(1000)  # 等待1秒
        await page.keyboard.press("End")

        await page.keyboard.press("Enter")

        # tag part
        for index, tag in enumerate(self.tags, start=1):
            tiktok_logger.info("Setting the %s tag" % index)
            await page.keyboard.press("End")
            await page.wait_for_timeout(1000)  # 等待1秒
            await page.keyboard.insert_text("#" + tag + " ")
            await page.keyboard.press("Space")
            await page.wait_for_timeout(1000)  # 等待1秒

            await page.keyboard.press("Backspace")
            await page.keyboard.press("End")

    async def upload_thumbnails(self, page):
        await self.locator_base.locator(".cover-container").click()
        await self.locator_base.locator(".cover-edit-container >> text=Upload cover").click()
        async with page.expect_file_chooser() as fc_info:
            await self.locator_base.locator(".upload-image-upload-area").click()
            file_chooser = await fc_info.value
            await file_chooser.set_files(self.thumbnail_path)
        await self.locator_base.locator('div.cover-edit-panel:not(.hide-panel)').get_by_role(
            "button", name="Confirm").click()
        await page.wait_for_timeout(3000)  # wait 3s, fix it later

    async def change_language(self, page):
        # 语言切换流程如果失败无需阻塞上传，增加容错
        try:
            await page.goto("https://www.tiktok.com")
            await page.wait_for_load_state('domcontentloaded')
            more_menu = page.locator('[data-e2e="nav-more-menu"]')
            await more_menu.wait_for(state='visible', timeout=10000)
            text = (await more_menu.text_content() or "").strip()
            if text and text.lower().startswith("more"):
                return

            await more_menu.click()
            language_entry = page.locator('[data-e2e="language-select"]')
            await language_entry.wait_for(state='visible', timeout=5000)
            await language_entry.click()

            english_option = page.locator('#creator-tools-selection-menu-header').locator("text=English (US)")
            await english_option.wait_for(state='visible', timeout=5000)
            await english_option.click()
        except Exception as exc:
            tiktok_logger.warning(f"[+] skip language switch: {exc}")

    async def click_publish(self, page):
        success_flag_div = 'div.common-modal-confirm-modal'
        while True:
            try:
                await self.ensure_modal_closed(page, wait_seconds=3)
                publish_button = self.locator_base.locator('div.button-group button').nth(0)
                if await publish_button.count():
                    await publish_button.click()
                    await self.ensure_modal_closed(page, wait_seconds=5)

                await page.wait_for_url("https://www.tiktok.com/tiktokstudio/content",  timeout=3000)
                tiktok_logger.success("  [-] video published success")
                break
            except Exception as e:
                tiktok_logger.exception(f"  [-] Exception: {e}")
                tiktok_logger.info("  [-] video publishing")
                await asyncio.sleep(0.5)

    async def get_last_video_id(self, page):
        await page.wait_for_selector('div[data-tt="components_PostTable_Container"]')
        video_list_locator = self.locator_base.locator('div[data-tt="components_PostTable_Container"] div[data-tt="components_PostInfoCell_Container"] a')
        if await video_list_locator.count():
            first_video_obj = await video_list_locator.nth(0).get_attribute('href')
            video_id = re.search(r'video/(\d+)', first_video_obj).group(1) if first_video_obj else None
            return video_id


    async def detect_upload_status(self, page):
        while True:
            try:
                # if await self.locator_base.locator('div.btn-post > button').get_attribute("disabled") is None:
                if await self.locator_base.locator(
                        'div.button-group > button >> text=Post').get_attribute("disabled") is None:
                    tiktok_logger.info("  [-]video uploaded.")
                    await self.ensure_modal_closed(page, wait_seconds=5)
                    break
                else:
                    tiktok_logger.info("  [-] video uploading...")
                    await asyncio.sleep(2)
                    if await self.locator_base.locator(
                            'button[aria-label="Select file"]').count():
                        tiktok_logger.info("  [-] found some error while uploading now retry...")
                        await self.handle_upload_error(page)
                    await self.ensure_modal_closed(page, wait_seconds=2)
            except:
                tiktok_logger.info("  [-] video uploading...")
                await asyncio.sleep(2)

    async def dismiss_auto_check_modal(self, page):
        handled = False
        try:
            dialog = page.get_by_role("dialog", name=re.compile("automatic content checks", re.I))
            if not await dialog.count():
                dialog = page.locator("div.common-modal").filter(has_text=re.compile("automatic content checks", re.I))
            if await dialog.count():
                cancel_btn = dialog.get_by_role("button", name=re.compile("cancel", re.I))
                if await cancel_btn.count():
                    await cancel_btn.click()
                    tiktok_logger.info("  [-] auto check modal closed via cancel button.")
                    await asyncio.sleep(0.5)
                    handled = True
                else:
                    close_btn = dialog.locator(".common-modal-close-icon")
                    if await close_btn.count():
                        await close_btn.click()
                        tiktok_logger.info("  [-] auto check modal closed via close icon.")
                        await asyncio.sleep(0.5)
                        handled = True
            if not handled:
                close_icon = page.locator("div.common-modal-close-icon").first
                if await close_icon.count():
                    await close_icon.click()
                    tiktok_logger.info("  [-] modal closed via global close icon.")
                    await asyncio.sleep(0.5)
                    handled = True
        except Exception as exc:
            tiktok_logger.warning(f"[+] dismiss auto check modal failed: {exc}")
        return handled

    async def ensure_modal_closed(self, page, wait_seconds=0):
        start_time = time.time()
        while True:
            handled = False
            if await self.dismiss_auto_check_modal(page):
                handled = True
            if await self.dismiss_continue_post_modal(page):
                handled = True
            if await self.dismiss_generic_cancelable_modal(page):
                handled = True
            if await self.wait_modal_overlay_hidden(page):
                handled = True
            if handled:
                await asyncio.sleep(0.3)
                continue
            if wait_seconds and (time.time() - start_time) < wait_seconds:
                await asyncio.sleep(0.5)
                continue
            break

    async def dismiss_generic_cancelable_modal(self, page):
        handled = False
        try:
            cancel_buttons = page.locator("div.common-modal button:has(.TUXButton-label:has-text('Cancel'))")
            while await cancel_buttons.count():
                await cancel_buttons.first.click()
                tiktok_logger.info("  [-] cancelable modal closed via cancel button.")
                await asyncio.sleep(0.5)
                handled = True
                cancel_buttons = page.locator("div.common-modal button:has(.TUXButton-label:has-text('Cancel'))")
        except Exception as exc:
            tiktok_logger.warning(f"[+] dismiss cancelable modal failed: {exc}")
        return handled

    async def dismiss_continue_post_modal(self, page):
        handled = False
        try:
            dialog = page.locator("div.common-modal").filter(has_text=re.compile("Continue to post", re.I))
            if not await dialog.count():
                dialog = page.get_by_role("dialog", name=re.compile("Continue to post", re.I))
            if await dialog.count():
                cancel_btn = dialog.locator("button:has(.TUXButton-label:has-text('Cancel'))")
                post_now_btn = dialog.locator("button:has(.TUXButton-label:has-text('Post now'))")
                if await cancel_btn.count():
                    await cancel_btn.click()
                    tiktok_logger.info("  [-] continue-post modal closed via cancel button.")
                    handled = True
                elif await post_now_btn.count():
                    await post_now_btn.click()
                    tiktok_logger.info("  [-] continue-post modal acknowledged via post now button.")
                    handled = True
                await asyncio.sleep(0.5)
        except Exception as exc:
            tiktok_logger.warning(f"[+] dismiss continue-post modal failed: {exc}")
        return handled

    async def wait_modal_overlay_hidden(self, page):
        try:
            overlay = page.locator("div.TUXModal-overlay[data-transition-status='open']")
            if await overlay.count():
                await overlay.wait_for(state='hidden', timeout=5000)
                return True
        except Exception as exc:
            tiktok_logger.warning(f"[+] wait overlay hidden failed: {exc}")
        return False

    async def choose_base_locator(self, page):
        # await page.wait_for_selector('div.upload-container')
        if await page.locator('iframe[data-tt="Upload_index_iframe"]').count():
            self.locator_base = page.frame_locator(Tk_Locator.tk_iframe)
        else:
            self.locator_base = page.locator(Tk_Locator.default) 

    async def main(self):
        async with async_playwright() as playwright:
            await self.upload(playwright)
