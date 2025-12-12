Способы обнаружения эксплуатации уязвимости XSS:

– логи веб-сервера: в файле `/app/logs/gunicorn-access.log` должен быть зафиксирован GET-запрос к `/xss-success/?tag=<script>alert('XSS')</script>` или POST-запрос к `/create-service-request/` с параметром `service_description`, содержащим JavaScript-код (например, `<script>...</script>`), а также GET-запрос оператора к `/review-request/<id>/` при просмотре заявки, содержащей XSS-пэйлоад в поле `service_description`;

– средства обнаружения вторжений: ViPNet IDS NS и Security Onion обнаруживают в сетевом трафике JavaScript-код, предназначенный для эксплуатации уязвимости XSS (например, теги `<script>`, функции `document.cookie`, `eval()`, `innerHTML` и другие признаки инъекции клиентского кода).

