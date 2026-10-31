"""Optional browser QA. Test offers stay in memory and are never shipped as application data."""
import asyncio
import json
import os
import tempfile
from pathlib import Path
import httpx
from playwright.async_api import async_playwright
from app import db, engine
from app.main import app
from unittest.mock import AsyncMock


async def main():
    os.environ['EPHEMERAL_STORAGE']='true'
    with tempfile.TemporaryDirectory() as directory:
        db.PATH=Path(directory)/'qa.sqlite3'
        engine.exchange_rate=AsyncMock(return_value=None)
        async with app.router.lifespan_context(app), httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='https://lowca.test') as client, async_playwright() as p:
            browser=await p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
            context=await browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,service_workers='block')
            async def route(r):
                req=r.request
                response=await client.request(req.method,req.url.replace('https://lowca.test',''),content=req.post_data,headers={'content-type':req.headers.get('content-type',''), 'origin':'https://lowca.test'})
                await r.fulfill(status=response.status_code,body=response.content,headers=dict(response.headers))
            await context.route('**/*',route)
            page=await context.new_page()
            errors=[]
            page.on('pageerror',lambda e: errors.append(str(e)))
            await page.goto('https://lowca.test/')
            await page.wait_for_selector('#portal-options input',state='attached')
            assert await page.locator('#portal-options input').count()==14
            if os.environ.get('QA_SCREENSHOT'):
                await page.screenshot(path=os.environ['QA_SCREENSHOT'],full_page=True)
            assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            await page.locator('[data-query="JUMZ"]').click()
            assert await page.locator('#query').input_value()=='JUMZ'
            await page.locator('#advanced summary').click()
            for checkbox in await page.locator('[name=portal]').all():
                await checkbox.uncheck()
            await page.locator('[name=portal][value=facebook]').check()
            await page.locator('#discovery').uncheck()
            await page.locator('#search-button').click()
            await page.wait_for_function("()=>document.querySelector('#progress-title').textContent==='Wyszukiwanie zakończone'")
            assert await page.locator('#results-count').text_content()=='0'
            await page.locator('#quality summary').click()
            assert 'Nie udało się przeszukać' in await page.locator('#reports').inner_text()
            owner=client.cookies.get('lowca_device')
            ident=db.history(owner)[0]['id']
            job=db.get_job(owner,ident)
            job['offers']=[dict(title='JUMZ test <script>bad()</script>',url='https://www.olx.pl/d/oferta/test-qa',price=15000,pln=15000,currency='PLN',country='PL',image=None,sold=False,new=False,portal='OLX',location='Miejscowość testowa',published=None,condition='Stan do weryfikacji',tax='Nie potwierdzono VAT')]
            db.save_job(job)
            await page.locator('[data-view=history]').click()
            assert await page.locator('.history-row').count()==1
            await page.locator('.history-row button').click()
            await page.wait_for_selector('.card')
            assert '<script>' in await page.locator('.card h3').inner_text()
            assert await page.locator('.card script').count()==0
            await page.locator('.favorite').click()
            await page.wait_for_function("()=>document.querySelector('#favorites-count').textContent==='1'")
            await page.locator('.hide').click()
            await page.locator('[data-view=hidden]').click()
            await page.wait_for_selector('.card')
            await page.locator('.hide').click()
            await page.locator('#help-button').click()
            assert await page.locator('#help').is_visible()
            await page.locator('#close-help').click()
            assert not errors, errors
            with db.connect() as connection:
                connection.execute('DELETE FROM searches')
                connection.execute('DELETE FROM settings')
                connection.execute('DELETE FROM saved')
            await page.reload()
            await page.wait_for_selector('#portal-options input',state='attached')
            assert await page.locator('#favorites-count').text_content()=='1'
            await page.locator('[data-view=history]').click()
            assert await page.locator('.history-row').count()==1
            await page.locator('.history-row button').click()
            await page.wait_for_function("()=>document.querySelector('#progress-message').textContent.includes('kopii na tym urządzeniu')")
            await page.set_viewport_size({'width':1280,'height':900})
            assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            await browser.close()
            print('Browser QA passed: mobile + desktop, search, history, report, help, no JS errors.')


if __name__ == '__main__': asyncio.run(main())
