""" get some pages from another wiki """

def run():
    import sys, os, xmlrpclib, codecs

    sys.path.insert(0, "..")
    from MoinMoin import wikiutil

    s = xmlrpclib.ServerProxy("http://wainu.ii.uned.es/wainuki/?action=xmlrpc2")
    index = open("index")

    for l in index:
        d = l.split('||')
        pn = d[3].strip()
        pd = s.getPage(pn)
        dn = wikiutil.quoteWikinameFS(pn.decode("utf-8"))
        os.mkdir(dn)
        cn = os.path.join(dn, 'current')
        f = open(cn, 'w')
        f.write('00000001\n')
        f.close()
        dn2 = os.path.join(dn, 'revisions')
        os.mkdir(dn2)
        fn = os.path.join(dn2, '00000001')
        f = codecs.open(fn, "wb", "utf-8")
        pd = pd.replace('\n', '\r\n')
        f.write(pd)
        f.close()

if __name__ == "__main__":
    run()

