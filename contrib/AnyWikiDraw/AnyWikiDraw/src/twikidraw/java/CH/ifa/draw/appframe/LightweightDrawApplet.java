// Copyright (C) 2001 Motorola - All rights reserved
package CH.ifa.draw.appframe;

import java.applet.Applet;
import java.awt.*;
import java.awt.event.*;
import java.util.*;
import java.io.*;
import java.net.*;

import CH.ifa.draw.framework.*;
import CH.ifa.draw.standard.*;
import CH.ifa.draw.figures.*;
import CH.ifa.draw.util.*;
import CH.ifa.draw.applet.*;
import CH.ifa.draw.contrib.*;

public abstract class LightweightDrawApplet extends Applet implements Application {
    
    private Frame frame;
    
    public void	init() {
        init(new DrawFrame("LightweightDrawApplet", this));
    }
    
    protected void init(Frame f) {
        frame = f;
        frame.pack();
        frame.show();
    }
    
    public void stop() {
        frame.hide();
        frame.dispose();
    }
    
    public void start() {
        frame.show();
    }
    
    /** Implement Application */
    public void showStatus(String s) {
        super.showStatus(s);
    }
    
    /** Implement Application */
    public String getParameter(String name) {
        return super.getParameter(name);
    }

    protected URL getURL(String rurl) throws IOException {
        return new URL(getCodeBase(), rurl);
    }

    /** Implement Application */
    public InputStream getStream(String relURL) throws IOException {
        return getURL(relURL).openStream();
    }
    
    /** Implement Application */
    public void popupFrame(String url, String name) {
        try {
            getAppletContext().showDocument(getURL(url), name);
        } catch (IOException e) {
            showStatus(name+" file not found");
        }
    }

    /** Implement Application */
    public abstract void exit();
}
