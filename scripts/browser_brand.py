"""Read-only UI checks. Blocks every HTTP mutation; never creates sessions or calls AI."""
from pathlib import Path
import argparse,json,os
from playwright.sync_api import sync_playwright,expect

BASE=os.getenv('SF_BROWSER_BASE_URL','http://127.0.0.1:5173')

def run(output,axe=None,channel=None):
    output.mkdir(parents=True,exist_ok=True)
    evidence={'theme_cases':[],'axe':[],'screenshots':[],'api_mutations':0,'paid_calls':0}
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(chromium_sandbox=True,channel=channel)
        def context(saved=None,scheme='light'):
            ctx=browser.new_context(viewport={'width':1440,'height':1000},color_scheme=scheme)
            def readonly(route):
                if route.request.method not in ('GET','HEAD','OPTIONS'):
                    raise AssertionError('Read-only brand regression attempted an HTTP mutation')
                route.continue_()
            ctx.route('**/*',readonly)
            if saved is not None:
                ctx.add_init_script('localStorage.setItem("arc-theme",'+json.dumps(saved)+');')
            return ctx
        def appearance(page,choice,resolved):
            expect(page.locator('html')).to_have_attribute('data-theme',resolved)
            expect(page.get_by_label('Tema da interface')).to_have_value(choice)
            expect(page.locator('meta[name="theme-color"]')).to_have_attribute('content','#0b1422' if resolved=='dark' else '#f3f6fa')
            expect(page.locator('.sf-brand .sf-logo-'+resolved)).to_be_visible()
            expect(page.locator('.sf-brand .sf-logo-'+('light' if resolved=='dark' else 'dark'))).to_be_hidden()
        # Inspect bootstrap independently: the React entry module is deliberately not loaded.
        early=context(scheme='light');p=early.new_page();p.route('**/src/main.jsx*',lambda route:route.abort())
        p.goto(BASE,wait_until='domcontentloaded')
        assert p.locator('html').get_attribute('data-theme')=='dark'
        assert p.locator('#root').inner_html()==''
        assert p.locator('meta[name="theme-color"]').get_attribute('content')=='#0b1422'
        evidence['before_react']='dark with a light OS preference';early.close()
        for saved in (None,'light','dark','auto'):
            for scheme in ('light','dark'):
                ctx=context(saved,scheme);p=ctx.new_page();p.goto(BASE)
                resolved=scheme if saved=='auto' else saved or 'dark'
                appearance(p,saved or 'dark',resolved)
                evidence['theme_cases'].append({'saved':saved,'system':scheme,'resolved':resolved})
                if saved=='auto':
                    opposite='light' if scheme=='dark' else 'dark'
                    p.emulate_media(color_scheme=opposite);appearance(p,'auto',opposite)
                ctx.close()
        # Persistence uses an unseeded context; reloading must retain the user's own selection.
        ctx=context();page=ctx.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(BASE);appearance(page,'dark','dark')
        for choice in ('light','dark','auto'):
            page.get_by_label('Tema da interface').select_option(choice)
            page.reload();appearance(page,choice,'light' if choice=='auto' else choice)
            assert page.evaluate('localStorage.getItem("arc-theme")')==choice
        for theme in ('dark','light'):
            page.get_by_label('Tema da interface').select_option(theme)
            for width in (1440,768,390):
                page.set_viewport_size({'width':width,'height':1000 if width>390 else 844})
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                logo=page.locator('.sf-brand .sf-logo-'+theme)
                assert logo.evaluate('img=>img.complete && img.naturalWidth===980 && img.naturalHeight===240')
                rect=logo.bounding_box();assert abs(rect['width']/rect['height']-980/240)<.02
                faq=page.locator('.sf-faq-section');box=faq.bounding_box()
                main=page.locator('.sf-main').bounding_box()
                assert abs(box['x']+box['width']/2-(main['x']+main['width']/2))<2
                assert faq.locator('h2').evaluate('el=>getComputedStyle(el.parentElement).textAlign')=='center'
                assert faq.locator('.sf-faq').evaluate('el=>getComputedStyle(el).textAlign')=='left'
                assert faq.locator('summary').count()==6
                assert page.get_by_text('Acesso técnico aos portais',exact=True).count()==0
                if width in (1440,390):
                    name=f'brand-{width}-{theme}.png';page.screenshot(path=str(output/name),full_page=True)
                    evidence['screenshots'].append(name)
                    if axe:
                        page.add_script_tag(path=str(axe))
                        violations=page.evaluate("async () => (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations")
                        evidence['axe'].append({'state':name,'violations':violations});assert not violations
        question=page.locator('.sf-faq summary').first;question.focus();page.keyboard.press('Enter')
        expect(question.locator('..')).to_have_attribute('open','');page.keyboard.press('Enter')
        technical=page.get_by_role('button',name='Acesso técnico',exact=True)
        technical.focus();page.keyboard.press('Enter')
        expect(page.get_by_label('Usuário',exact=True)).to_be_focused()
        expect(page.get_by_label('Senha',exact=True)).to_be_visible()
        technical.click();expect(page.get_by_label('Usuário',exact=True)).to_be_hidden()
        evidence['faq_and_technical']='centered; six FAQs; keyboard expands; footer opens existing login'
        assert not errors,errors
        # Chromium's reserved /favicon.ico handling conflicts with intercepting all
        # resources (even nonmatching routes disable the resource cache). Decode
        # on a static, image-only page with no app code, scripts, forms or API calls.
        app_page=page
        icon_context=browser.new_context(viewport={'width':800,'height':520})
        page=icon_context.new_page();page.set_content('<html lang="pt-BR"><title>Ícones</title></html>')
        assets={}
        for name,mime in [('favicon.svg','image/svg+xml'),('favicon.ico','image/'),('apple-touch-icon.png','image/png')]:
            response=page.request.get(BASE+'/'+name);assert response.status==200
            assert mime in response.headers['content-type']
            decoded=page.evaluate('''async url => {const img=new Image(); img.src=url;try{await img.decode();return {ok:img.naturalWidth>0 && img.naturalHeight>0};}catch(error){return {ok:false,error:error.name};}}''',BASE+'/'+name)
            assert decoded['ok'],(name,decoded)
            assets[name]={'status':response.status,'type':response.headers['content-type']}
        assert app_page.locator('link[rel="icon"][type="image/svg+xml"]').get_attribute('href')=='/favicon.svg'
        assert app_page.locator('link[rel="icon"][type="image/x-icon"]').get_attribute('href')=='/favicon.ico'
        assert app_page.locator('link[rel="apple-touch-icon"]').get_attribute('sizes')=='180x180'
        evidence['icons']=assets
        # Recognizability at native icon sizes on both backgrounds, using supplied SVG and ICO.
        page.set_viewport_size({'width':800,'height':520})
        page.set_content('''<html lang="pt-BR"><head><title>Ícones SolicitaFlow</title></head><body style="margin:0;font:18px Arial">'''+''.join('<section style="padding:32px;background:'+bg+';color:'+fg+'"><p>SVG e ICO · 16 / 32 / 48 px</p>'+''.join(f'<img alt="{fmt} {size}px" src="{BASE}/favicon.{fmt}" width="{size}" height="{size}" style="margin:12px;vertical-align:middle">' for fmt in ('svg','ico') for size in (16,32,48))+'</section>' for bg,fg in (('#0b1422','#eaf6ff'),('#f3f6fa','#10233d')) )+'</body></html>')
        page.locator('img').evaluate_all('imgs=>Promise.all(imgs.map(img=>img.decode()))')
        page.screenshot(path=str(output/'favicons-small.png'));evidence['screenshots'].append('favicons-small.png')
        icon_context.close();ctx.close()
        fallback=context();p=fallback.new_page();p.route('**/theme-init.js*',lambda route:route.abort());p.goto(BASE)
        appearance(p,'dark','dark');fallback.close();evidence['react_fallback']='dark without bootstrap'
        browser.close()
    evidence['passed']=True
    (output/'browser-brand.json').write_text(json.dumps(evidence,indent=2,ensure_ascii=False))
    print('Brand UI passed: 8 saved/system combinations, automatic live changes, persisted choices, bootstrap, FAQ, icons and responsive themes; no HTTP mutations or paid calls.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=Path('/tmp/solicitaflow-brand-captures'));parser.add_argument('--axe',type=Path)
    parser.add_argument('--channel',choices=['chrome','msedge','chromium'])
    args=parser.parse_args();run(args.output,args.axe,args.channel)
