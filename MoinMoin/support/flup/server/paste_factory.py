def helper(wsgiServerClass, global_conf, host, port, **local_conf):
    # I think I can't write a tuple for bindAddress in .ini file
    host = host or global_conf.get('host', 'localhost')
    port = port or global_conf.get('port', 4000)

    if 'socket' in local_conf:
        local_conf['bindAddress'] = local_conf['socket']
        del local_conf['socket']
    else:
        local_conf['bindAddress'] = (host, int(port))
    
    def server(application):
        server = wsgiServerClass(application, **local_conf)
        server.run()

    return server
