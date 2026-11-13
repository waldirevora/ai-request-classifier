"""Onboarding regression helpers; real session expiry/quota exhaustion live in pytest.

Browser 401/429 fixtures exercise UI recovery without expiring user sessions or
exhausting shared local quotas. Authentication fixtures stay in private CLI files.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import json,os
from playwright.sync_api import expect

BASE = os.getenv('SF_BROWSER_BASE_URL','http://127.0.0.1:5173')
HEADERS = {'X-SolicitaFlow-Context': 'lab'}


def fit_and_readable(page):
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Document overflow'
    small = page.evaluate('''() => [...document.querySelectorAll('main p,main small,main label,main time,.badge,button,summary,td,th')]
      .filter(el => {const r=el.getBoundingClientRect();return r.width>5 && r.height>5 && getComputedStyle(el).visibility!=='hidden'})
      .filter(el => parseFloat(getComputedStyle(el).fontSize)<14)
      .map(el => ({tag:el.tagName,classes:el.className,size:getComputedStyle(el).fontSize}))''')
    assert not small, small


def initial_entry(page, context, shot, accessibility, evidence, creation_posts):
    expect(page.get_by_role('heading',name='Sua empresa recebe solicitações. Mas consegue acompanhar todas até a resolução?')).to_be_visible()
    assert not creation_posts
    for mode in ('light', 'dark'):
        page.get_by_label('Tema da interface').select_option(mode)
        for width in (1440, 390):
            page.set_viewport_size({'width': width, 'height': 1000})
            fit_and_readable(page)
            name = f'home-{width}-{mode}'
            shot(name); accessibility(name)
    page.set_viewport_size({'width': 1440, 'height': 1000})
    page.evaluate("document.documentElement.style.fontSize='200%'")
    fit_and_readable(page);shot('home-text-200-percent')
    page.evaluate("document.documentElement.style.fontSize=''")
    question = page.get_by_text('A inteligência artificial resolve as solicitações?', exact=True)
    question.focus(); page.keyboard.press('Enter')
    expect(question.locator('..')).to_have_attribute('open', '')
    page.keyboard.press('Enter')

    # Two tabs share cookies/locks, not IP identity. Both click while unauthenticated.
    sibling = context.new_page(); sibling.goto(BASE)
    expect(sibling.get_by_role('heading',name='Sua empresa recebe solicitações. Mas consegue acompanhar todas até a resolução?')).to_be_visible()
    sibling.evaluate('''() => {
      window.entryChannel = new BroadcastChannel('sf25-entry-test');
      entryChannel.onmessage = () => document.querySelector('.sf-welcome .button.primary').click();
    }''')
    page.evaluate('''() => {
      window.entryChannel = new BroadcastChannel('sf25-entry-test'); entryChannel.postMessage('enter');
      const button = document.querySelector('.sf-welcome .button.primary'); button.click(); button.click();
    }''')
    for active in (page, sibling):
        expect(active.get_by_role('heading', name='Portal do Colaborador')).to_be_visible()
    assert len(creation_posts) == 1, creation_posts
    sibling.close()
    who = page.request.get(BASE+'/api/v2/session', headers=HEADERS).json()
    page.reload(); expect(page.get_by_role('heading', name='Portal do Colaborador')).to_be_visible()
    assert len(creation_posts) == 1
    page.get_by_role('button', name='Voltar ao ambiente local', exact=True).click()
    expect(page.get_by_role('heading',name='Sua empresa recebe solicitações. Mas consegue acompanhar todas até a resolução?')).to_be_visible()
    page.locator('.sf-welcome').get_by_role('button', name='Experimentar o SolicitaFlow', exact=True).click()
    expect(page.get_by_role('heading', name='Portal do Colaborador')).to_be_visible()
    assert page.request.get(BASE+'/api/v2/session', headers=HEADERS).json()['workspace_id'] == who['workspace_id']
    assert len(creation_posts) == 1
    evidence['onboarding'] = ['educational landing', 'readable light/dark desktop/mobile', '200% text resize', 'keyboard FAQ', 'double click and concurrent tabs: one creation', 'reload without creation', 'return and resume without creation']


def finish_entry_checks(page, browser, context, output, evidence, creation_posts):
    before = page.request.get(BASE+'/api/v2/cases', headers=HEADERS).json()
    clock = page.request.get(BASE+'/api/v2/lab/clock', headers=HEADERS).json()
    page.get_by_text('Ver o roteiro e recomeçar a orientação', exact=True).click()
    page.get_by_role('button', name='Recomeçar roteiro', exact=True).click()
    expect(page.get_by_role('status')).to_contain_text('Pedidos, histórico e relógio foram preservados')
    assert len(creation_posts) == 1
    after = page.request.get(BASE+'/api/v2/cases', headers=HEADERS).json()
    assert {item['id'] for item in before} == {item['id'] for item in after}
    from datetime import datetime
    new_clock = page.request.get(BASE+'/api/v2/lab/clock', headers=HEADERS).json()
    assert abs((datetime.fromisoformat(new_clock['effective_now'])-datetime.fromisoformat(clock['effective_now'])).total_seconds()) < 10

    # Explicitly simulated UI expiration; never modify a live visitor's DB session.
    context.route('**/api/v2/session', lambda route: route.fulfill(status=401, content_type='application/json', body=json.dumps({'detail':'Sessão expirada. Entre novamente.'})))
    page.reload()
    expect(page.get_by_text('Sua sessão de demonstração encerrou.',exact=True)).to_be_visible()
    assert len(creation_posts) == 1
    context.unroute('**/api/v2/session')

    limited = browser.new_context(viewport={'width':390,'height':844})
    quota_page = limited.new_page(); attempts=[]
    def deny(route):
        attempts.append(1)
        route.fulfill(status=429,headers={'Retry-After':'120'},content_type='application/json',body=json.dumps({'detail':'Muitas demonstrações novas foram iniciadas nesta rede. Aguarde para criar outra.'}))
    quota_page.route('**/api/v2/lab/start', deny)
    quota_page.goto(BASE)
    for _ in range(2):
        quota_page.locator('.sf-welcome').get_by_role('button', name='Experimentar o SolicitaFlow', exact=True).click()
        expect(quota_page.get_by_role('alert')).to_contain_text('Você poderá criar uma nova demonstração às')
    assert len(attempts) == 1
    quota_page.screenshot(path=str(output/'home-mobile-429.png'),full_page=True)
    evidence['screenshots'].append('home-mobile-429.png')
    fit_and_readable(quota_page)
    limited.close()
    evidence['onboarding'] += ['restart preserves requests and clock', 'expired-session UI requires explicit new entry (401 fixture)', '429 Retry-After UI and no automatic repeat (429 fixture)']


def authenticated_portal(browser, accounts_path, evidence):
    assert accounts_path.exists(), 'Private local/CI fixture accounts are required for authenticated portal regression'
    assert accounts_path.stat().st_mode & 0o077 == 0, 'Account fixture must remain private'
    account = next(a for a in json.loads(accounts_path.read_text())['accounts'] if a['username']=='central')
    context = browser.new_context(viewport={'width':1440,'height':1000})
    # The legacy paid path must remain read-only throughout this browser regression.
    context.route('**/api/solicitacoes', lambda route: route.continue_() if route.request.method=='GET' else route.abort())
    page=context.new_page();page.goto(BASE)
    page.get_by_text('Acesso técnico aos portais',exact=True).click()
    page.get_by_label('Usuário',exact=True).fill(account['username'])
    page.get_by_label('Senha',exact=True).fill(account['password'])
    page.get_by_role('button',name='Entrar',exact=True).click()
    expect(page.get_by_role('heading',name='Central Operacional',exact=True)).to_be_visible()
    page.get_by_role('button',name='Triagem clássica',exact=True).click()
    for width in (1440,390):
        page.set_viewport_size({'width':width,'height':1000})
        for tab in ('Visão geral','Nova solicitação','Triagem e revisão','Como funciona'):
            page.get_by_role('tab',name=tab,exact=False).click()
            fit_and_readable(page)
    page.get_by_label('Tema da interface',exact=True).select_option('dark')
    page.get_by_role('button',name='← Voltar aos portais SolicitaFlow',exact=True).click()
    expect(page.get_by_label('Tema da interface',exact=True)).to_have_value('dark')
    context.close()
    evidence['onboarding'] += ['authenticated local portal and four classic tabs', 'theme preserved across portal/classic navigation']


def native_zoom(playwright, channel, output, evidence, lab_cookies, axe):
    with TemporaryDirectory(prefix='solicitaflow-zoom-') as profile:
        context=playwright.chromium.launch_persistent_context(profile,channel=channel or 'chromium',chromium_sandbox=True,no_viewport=True,args=['--window-size=1440,1000'])
        page=context.pages[0]
        # Native browser setting in a disposable profile; no CSS/CDP scaling substitute.
        page.goto('chrome://settings/appearance')
        page.locator('select#zoomLevel').select_option('2')
        page.goto(BASE)
        expect(page.get_by_role('heading',name='Sua empresa recebe solicitações. Mas consegue acompanhar todas até a resolução?')).to_be_visible()
        metrics=page.evaluate('({innerWidth,outerWidth,devicePixelRatio})')
        assert metrics['devicePixelRatio']==2 and metrics['innerWidth']==720, metrics
        fit_and_readable(page)
        page.screenshot(path=str(output/'home-native-zoom-200.png'),full_page=True)
        evidence['native_zoom_200_percent']=metrics
        evidence['screenshots'].append('home-native-zoom-200.png')
        # Transfer only this test visitor's still-valid lab capability in memory.
        # No recovery mechanism, IP identity, expired session or local account is used.
        context.add_cookies([cookie for cookie in lab_cookies if cookie['name']=='sf_lab'])
        context.route('**/api/v2/lab/start',lambda route:route.abort())
        page.evaluate("sessionStorage.setItem('sf-context','lab')")
        page.reload()
        expect(page.get_by_role('heading',name='Portal do Colaborador')).to_be_visible()
        page.locator('.sf-list-item').first.click()
        expect(page.locator('.sf-detail')).to_be_visible()
        page.get_by_label('Tema da interface').select_option('dark')
        fit_and_readable(page)
        page.screenshot(path=str(output/'lab-native-zoom-200-dark.png'),full_page=True)
        evidence['screenshots'].append('lab-native-zoom-200-dark.png')
        if axe:
            page.add_script_tag(path=str(axe))
            violations=page.evaluate("async () => (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations")
            evidence['axe'].append({'state':'lab-native-zoom-200-dark','violations':violations})
            assert not violations,[(v['id'],v['impact']) for v in violations]
        context.close()
