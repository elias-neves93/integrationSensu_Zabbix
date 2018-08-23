#-*- coding: utf-8 -*-
from pyzabbix import ZabbixAPI, ZabbixAPIException
import requests
import json
import time

zabbix_server= 'https://zabbix-cloud.ns2online.com.br'

zapi = ZabbixAPI(zabbix_server)
zapi.session.verify = False
zapi.login('user', 'pass')

host_name = 'Sensu Items'

def get_id_items_zabbix() -> str:
    list_ids = []

    items = zapi.item.get(filter={"host": host_name})
    for item in range(len(items)):
        name = items[item]['name'].split(" ")
        name_id = name[0]
        list_ids.append({'name_id':name_id,'item_id':items[item]['itemid']})
    return list_ids


def delete_item_zabbix(item_id) -> str:

    zapi.item.delete(item_id)
    return 'Item {} deletado!'.format(item_id)

def get_items_sensu_api() -> str:

    list_sensu = []
    url_sensu = 'http://nsmonitor.ns2online.com.br/events'

    r = requests.get(url_sensu, headers={'Content-Type':'application/json'})
    result = json.loads(r.text)

    for i in range(len(result)):
        id = result[i]["id"]
        severidade = result[i]["check"]["status"]
        output = result[i]["check"]["output"]
        host = result[i]["client"]["name"]
        silenced = result[i]["silenced"]
        if severidade == 2 and silenced == False:
            list_sensu.append({'id':id,'host':host,'output':output[:255],'severidade':severidade,'silenced':silenced})

    return list_sensu

def items_zabbix() -> str:

    while True:

        lista_sensu = get_items_sensu_api()
        lista_zabbix = get_id_items_zabbix()

        # Criando items do Sensu no Zabbix
        if len(lista_sensu) != 0:
            for i in range(len(lista_sensu)):

                try:

                    item = zapi.item.create(
                    hostid=11253,
                    name='{} - {} - {}'.format(lista_sensu[i]['id'], lista_sensu[i]['host'], lista_sensu[i]['output']),
                    key_='sensu[{}]'.format(lista_sensu[i]['id']),
                    type=0,
                    value_type=0,
                    delay=10,
                    applications=[7367]
                    )

                    extrigger='''{0}Sensu Items:sensu[{1}].last(){2}=0'''.format('{',lista_sensu[i]['id'],'}')

                    trigger = zapi.trigger.create(
                    description='{} - {}'.format(lista_sensu[i]['host'], lista_sensu[i]['output']),
                    expression=extrigger,
                    url='https://confluence.ns2online.com.br/display/SSC/POP%3A+New+Relic+account+Netshoes+-+Inka',
                    priority=4
                    )

                    ids_items_sensu = []

                    for j in range(len(lista_sensu)):
                        ids_items_sensu.append(lista_sensu[j]['id'])


                    for id_zabbix in range(len(lista_zabbix)):
                        print('comparando o ID ZABBIX com o do SENSU. \n ID: '+lista_zabbix[id_zabbix]['name_id'])
                        if lista_zabbix[id_zabbix]['name_id'] not in ids_items_sensu:
                            print('Item do Zabbix não existe no Sensu. Excluindo...')
                            delete_item_zabbix(lista_zabbix[id_zabbix]['item_id'])
                            time.sleep(1)
                        else:
                            print('Item: {} existe no Sensu'.format(lista_zabbix[id_zabbix]['name_id']))
                            time.sleep(1)


                except ZabbixAPIException as e:

                    print('O Item já existe.\n Aguardando 2 Segundos...')
                    time.sleep(2)
                    print('Erro: {}'.format(e))



if __name__ == "__main__":
    items_zabbix()
