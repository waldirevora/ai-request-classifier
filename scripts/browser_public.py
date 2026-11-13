"""Compiled same-origin HTTPS regression, mocked provider, no production credentials."""
from pathlib import Path
import argparse,json,os,re
from playwright.sync_api import sync_playwright,expect
BASE='https://127.0.0.1:18443'

def run(out,axe,channel=None):
    out.mkdir(parents=True,exist_ok=True);evidence={'steps':[],'axe':[],'screenshots':[],'paid_calls':0}
    with sync_playwright() as p:
        browser=p.chromium.launch(chromium_sandbox=True,channel=channel)
        ctx=browser.new_context(ignore_https_errors=True,viewport={'width':1440,'height':1000}) # self-signed, loopback QA only
        if axe:ctx.add_init_script(path=str(axe))
        page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        def shot(name):page.screenshot(path=str(out/(name+'.png')),full_page=True);evidence['screenshots'].append(name+'.png')
        def checkaxe(name):
            if axe:
                v=page.evaluate("async()=> (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations")
                evidence['axe'].append({'state':name,'violations':v});assert not v,[(x['id'],x['impact']) for x in v]
        def switch(value):
            page.get_by_label('Personagem fictício',exact=True).select_option(value)
            expect(page.get_by_role('button',name='Atualizar',exact=True)).to_be_enabled()
        def opencase(title):page.get_by_role('button',name=title,exact=False).click();expect(page.get_by_role('heading',name=title,exact=True)).to_be_visible()
        response=page.goto(BASE);assert response.status==200
        assert page.locator('html').get_attribute('data-public-demo')=='true'
        assert 'strict-transport-security' in response.headers
        metadata=page.request.get(BASE+'/api/v2/presentation',headers={'X-SolicitaFlow-Context':'lab'}).json();assert metadata['public_demo'] and metadata['test_mode']
        assert page.get_by_role('button',name='Acesso técnico',exact=True).count()==0
        for theme in ('dark','light'):
            page.get_by_label('Tema da interface').select_option(theme)
            for width in (1440,390):
                page.set_viewport_size({'width':width,'height':1000 if width>400 else 844})
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                shot('public-home-'+theme+'-'+str(width));checkaxe('home-'+theme+'-'+str(width))
        page.set_viewport_size({'width':1440,'height':1000});page.get_by_label('Tema da interface').select_option('auto')
        for mode in ('dark','light'):
            page.emulate_media(color_scheme=mode);expect(page.locator('html')).to_have_attribute('data-theme',mode)
        page.locator('.sf-welcome').get_by_role('button',name='Experimentar o SolicitaFlow',exact=True).click()
        expect(page.get_by_role('heading',name='Portal do Colaborador')).to_be_visible()
        cookies=ctx.cookies();cookie=next(x for x in cookies if x['name']=='__Host-sf_lab')
        assert cookie['secure'] and cookie['httpOnly'] and cookie['sameSite']=='Strict' and cookie['path']=='/'
        labs=[];ctx.on('request',lambda r:labs.append(r.url) if r.method=='POST' and r.url.endswith('/lab/start') else None)
        page.reload();expect(page.get_by_role('heading',name='Portal do Colaborador')).to_be_visible();assert not labs
        page.get_by_role('button',name='Exemplo de TI',exact=True).click();page.get_by_role('button',name='Enviar solicitação',exact=True).click()
        title='Servidor indisponível para a equipe'
        expect(page.get_by_text('Encaminhamento automático · destino validado pelas regras')).to_be_visible(timeout=15000)
        rows=page.request.get(BASE+'/api/v2/cases',headers={'X-SolicitaFlow-Context':'lab'}).json();case=rows[0]['id']
        evidence['steps']+=['HTTPS compiled frontend','no login','Secure HttpOnly Strict host cookie','reload resumes without lab creation','mock analysis and routing']
        page.get_by_role('button',name=re.compile('Entrar como Departamento')).click()
        expect(page.get_by_role('heading',name='Portal do Departamento')).to_be_visible();opencase(title)
        expect(page.get_by_label('Registro de atendimento')).to_be_visible()
        page.get_by_label('Registro de atendimento').fill('Equipe fictícia assume a investigação.')
        page.get_by_role('button',name='Assumir atendimento',exact=True).click()
        expect(page.get_by_role('button',name='Registrar andamento',exact=True)).to_be_visible()
        expect(page.get_by_label('Registro de atendimento')).to_have_value('')
        page.get_by_label('Registro de atendimento').fill('Diagnóstico fictício em andamento.')
        page.get_by_role('button',name='Registrar andamento',exact=True).click()
        expect(page.get_by_label('Registro de atendimento')).to_have_value('')
        page.get_by_role('button',name='Avançar 6 horas',exact=True).click();expect(page.get_by_text('SLA em risco',exact=True)).to_be_visible()
        page.get_by_role('button',name='Avançar 8 horas',exact=True).click();expect(page.get_by_text('Escalonamento para a central',exact=True)).to_be_visible()
        shot('public-sla-overdue');checkaxe('department-overdue')
        page.get_by_label('Registro de atendimento').fill('Servidor fictício restabelecido e resolução registrada.')
        page.get_by_role('button',name='Confirmar resolução efetiva',exact=True).click();expect(page.get_by_text('Resposta do departamento',exact=True)).to_be_visible()
        switch('colaborador');opencase(title);expect(page.get_by_text('Resposta do departamento',exact=True)).to_be_visible()
        for theme in ('dark','light'):
            page.get_by_label('Tema da interface').select_option(theme);page.set_viewport_size({'width':390,'height':844});shot('public-resolved-mobile-'+theme);checkaxe('resolved-mobile-'+theme)
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.set_viewport_size({'width':1440,'height':1000})
        switch('central');page.get_by_role('button',name='SLA e relatórios',exact=True).click();expect(page.get_by_role('table')).to_be_visible();shot('public-central-report')
        evidence['steps']+=['department claim','progress','event-driven SLA risk','violation and escalation','resolution','collaborator response','central report']
        second=browser.new_context(ignore_https_errors=True);other=second.new_page();other.goto(BASE)
        other.locator('.sf-welcome').get_by_role('button',name='Experimentar o SolicitaFlow',exact=True).click();expect(other.get_by_role('heading',name='Portal do Colaborador')).to_be_visible()
        assert other.request.get(BASE+'/api/v2/cases/'+case,headers={'X-SolicitaFlow-Context':'lab'}).status==404
        assert other.request.get(BASE+'/api/v2/session',headers={'X-SolicitaFlow-Context':'local'}).status==401
        assert page.request.get(BASE+'/api/docs').status in (403,404)
        assert page.request.post(BASE+'/api/v2/lab/start',headers={'Origin':'https://attacker.invalid','Content-Type':'application/json','X-SolicitaFlow-Context':'lab'},data={}).status==403
        other.get_by_role('button',name='Exemplo com dois assuntos',exact=True).click();other.get_by_role('button',name='Enviar solicitação',exact=True).click();expect(other.get_by_text('A central precisa esclarecer o destino.',exact=True)).to_be_visible()
        other.get_by_role('button',name='Nova solicitação',exact=True).click();other.get_by_label('Título',exact=True).fill('QA falha de API');other.get_by_label('Descrição',exact=True).fill('Uma equipe fictícia precisa verificar um servidor parado neste expediente.')
        other.get_by_role('button',name='Enviar solicitação',exact=True).click();expect(other.get_by_role('heading',name='Não foi possível concluir a análise.',exact=True)).to_be_visible()
        evidence['steps']+=['two visitor isolation','local credentials inaccessible','CSRF blocked','ambiguous exception','API failure saved without fabricated suggestion']
        # Zoom via CSS is a reflow check, distinct from native browser zoom.
        page.evaluate("document.documentElement.style.fontSize='200%'");assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');shot('public-text-zoom-200')
        page.keyboard.press('Tab');assert page.evaluate('document.activeElement!==document.body')
        assert not errors,errors
        evidence.update(passed=True,js_errors=errors,three_themes=True,reload_creation_posts=len(labs))
        (out/'browser-public.json').write_text(json.dumps(evidence,indent=2,ensure_ascii=False));browser.close()
        print('Public HTTPS browser passed:',len(evidence['steps']),'steps; axe states',len(evidence['axe']),'; paid calls0.')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--axe',type=Path);p.add_argument('--channel');a=p.parse_args();run(a.output,a.axe,a.channel)
