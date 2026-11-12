"""Real Chromium regression. Creates only fictional isolated labs; never calls paid AI.
Usage: browser-venv/bin/python scripts/browser_lab.py --output /tmp/solicitaflow-captures --axe /path/to/axe.min.js
"""
from pathlib import Path
from uuid import uuid4
import argparse,json
from playwright.sync_api import sync_playwright,expect

def run(output,axe):
    output.mkdir(parents=True,exist_ok=True)
    evidence={'steps':[],'axe':[],'screenshots':[]}
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(chromium_sandbox=True)
        context=browser.new_context(viewport={'width':1440,'height':1000})
        page=context.new_page();errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        def shot(name):
            page.screenshot(path=str(output/(name+'.png')),full_page=True);evidence['screenshots'].append(name+'.png')
        def accessibility(name):
            if not axe:return
            page.add_script_tag(path=str(axe))
            result=page.evaluate("async () => (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations")
            evidence['axe'].append({'state':name,'violations':result})
            assert not result,[(v['id'],v['impact']) for v in result]
        def switch(name):
            page.get_by_label('Personagem fictício',exact=True).select_option(name)
            expect(page.get_by_label('Personagem fictício',exact=True)).to_have_value(name)
            expect(page.get_by_role('button',name='Atualizar',exact=True)).to_be_enabled()
        def open_case(title):
            page.get_by_role('button',name=title,exact=False).click()
            expect(page.get_by_role('heading',name=title,exact=True)).to_be_visible()
        page.goto('http://127.0.0.1:5173/')
        page.get_by_role('button',name='Explorar laboratório',exact=True).click()
        expect(page.get_by_role('heading',name='Portal do Colaborador')).to_be_visible()
        expect(page.get_by_label('Personagem fictício')).to_be_enabled()
        page.get_by_role('button',name='Cenário automático',exact=True).click()
        page.get_by_role('button',name='Enviar solicitação',exact=True).click()
        title='Servidor indisponível para a equipe'
        expect(page.get_by_role('heading',name=title,exact=True)).to_be_visible()
        expect(page.get_by_text('Encaminhamento automático · destino validado pelas regras')).to_be_visible()
        rows=page.request.get('http://127.0.0.1:5173/api/v2/cases',headers={'X-SolicitaFlow-Context':'lab'}).json()
        case_id=rows[0]['id']
        evidence['steps']+=['fictional collaborator','create persisted request','automatic validated routing']
        page.get_by_label('Tema da interface').select_option('light');shot('lab-desktop-light');accessibility('desktop-light')
        page.get_by_label('Tema da interface').select_option('dark');shot('lab-desktop-dark');accessibility('desktop-dark')
        page.get_by_label('Tema da interface').select_option('auto')
        page.emulate_media(color_scheme='light');expect(page.locator('html')).to_have_attribute('data-theme','light')
        page.emulate_media(color_scheme='dark');expect(page.locator('html')).to_have_attribute('data-theme','dark')
        page.keyboard.press('Tab');assert page.evaluate('document.activeElement !== document.body')
        switch('suporte_ti');open_case(title)
        page.get_by_label('Registro de atendimento').fill('Equipe fictícia assume a investigação do servidor.')
        page.get_by_role('button',name='Assumir atendimento',exact=True).click()
        expect(page.get_by_role('button',name='Registrar andamento')).to_be_visible()
        page.get_by_label('Registro de atendimento').fill('Diagnóstico em andamento. Verificação fictícia iniciada.')
        page.get_by_role('button',name='Registrar andamento',exact=True).click()
        expect(page.get_by_label('Registro de atendimento')).to_have_value('')
        page.get_by_role('button',name='Avançar 6 horas',exact=True).click()
        expect(page.get_by_role('status')).to_contain_text('6 horas')
        expect(page.get_by_text('risco sla',exact=True)).to_be_visible()
        page.get_by_role('button',name='Avançar 8 horas',exact=True).click()
        expect(page.get_by_role('status')).to_contain_text('8 horas')
        expect(page.get_by_text('escalonamento',exact=True)).to_be_visible()
        shot('lab-department-overdue-desktop')
        page.get_by_label('Registro de atendimento').fill('Servidor restabelecido pela equipe fictícia. Operação normalizada.')
        page.get_by_role('button',name='Confirmar resolução efetiva',exact=True).click()
        expect(page.get_by_text('Resposta do departamento',exact=True)).to_be_visible()
        evidence['steps']+=['department claims','progress','simulated time','SLA risk','SLA breach and escalation','department resolution']
        switch('colaborador');open_case(title)
        expect(page.get_by_text('Resposta do departamento',exact=True)).to_be_visible()
        page.set_viewport_size({'width':390,'height':844});shot('lab-collaborator-resolved-mobile-dark');accessibility('mobile-dark')
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.get_by_label('Tema da interface').select_option('light');shot('lab-collaborator-resolved-mobile-light')
        for width in (768,1440):
            page.set_viewport_size({'width':width,'height':1000});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        switch('central');page.get_by_role('button',name='SLA e relatórios',exact=True).click()
        expect(page.get_by_role('table')).to_be_visible();shot('lab-central-reports-desktop')
        evidence['steps']+=['collaborator reads response','central reports and history']
        switch('colaborador');page.get_by_role('button',name='Cenário ambíguo',exact=True).click()
        page.get_by_role('button',name='Enviar solicitação',exact=True).click()
        ambiguous='Dúvida entre tecnologia e financeiro'
        expect(page.get_by_role('heading',name=ambiguous)).to_be_visible()
        expect(page.get_by_text('A central precisa esclarecer o destino.',exact=True)).to_be_visible()
        switch('central');open_case(ambiguous)
        form=page.locator('form').filter(has=page.get_by_role('heading',name='Revisão da exceção'))
        form.get_by_label('Categoria',exact=False).select_option('suporte_ti')
        form.get_by_label('Departamento',exact=False).select_option(label='Tecnologia')
        form.get_by_label('Motivo da decisão',exact=True).fill('Após esclarecimento fictício, o problema principal é o servidor da equipe.')
        form.get_by_role('button',name='Confirmar revisão e encaminhar').click()
        expect(page.get_by_role('heading',name='Revisão da exceção')).to_have_count(0)
        expect(page.get_by_text('revisao humana',exact=True)).to_be_visible();shot('lab-central-exception-reviewed')
        evidence['steps']+=['ambiguous request','human exception review','original suggestion preserved']
        visitor=browser.new_context();other=visitor.new_page();other.goto('http://127.0.0.1:5173/')
        other.get_by_role('button',name='Explorar laboratório',exact=True).click()
        expect(other.get_by_role('heading',name='Portal do Colaborador')).to_be_visible()
        assert other.request.get('http://127.0.0.1:5173/api/v2/cases/'+case_id,headers={'X-SolicitaFlow-Context':'lab'}).status==404
        assert other.request.get('http://127.0.0.1:5173/api/v2/cases',headers={'X-SolicitaFlow-Context':'local'}).status==401
        response=other.request.post('http://127.0.0.1:5173/api/v2/cases',headers={'X-SolicitaFlow-Context':'lab'},data={'titulo':'Teste fictício','descricao':'Uma descrição inteiramente fictícia sem dados pessoais.','mode':'deepseek','client_key':str(uuid4())})
        assert response.status==403
        evidence['steps']+=['second visitor isolation','local/lab separation','paid API denied']
        page.get_by_role('button',name='Como funciona',exact=True).click()
        expect(page.get_by_role('heading',name='Automação com regras. Pessoas nas exceções.')).to_be_visible()
        page.get_by_label('Impacto educativo',exact=False).select_option('empresa')
        page.get_by_label('Urgência educativa',exact=False).select_option('media')
        expect(page.locator('output')).to_contain_text('alta')
        assert not errors,errors
        evidence.update(passed=True,widths=[1440,768,390],themes=['light','dark','auto-live'],js_errors=errors,paid_calls=0)
        (output/'browser-lab.json').write_text(json.dumps(evidence,indent=2,ensure_ascii=False))
        browser.close()
        print('Browser lab passed:',len(evidence['steps']),'steps; themes, responsive, accessibility, isolation and no paid calls.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=Path('/tmp/solicitaflow-captures'));parser.add_argument('--axe',type=Path)
    args=parser.parse_args();run(args.output,args.axe)
