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

public  class LightweightDrawApplet extends Applet implements Application {

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

    /** Implement Application */
    public URL getURL(String relURL) throws MalformedURLException {
	return new URL(getCodeBase(), relURL);
    }

    /** Implement Application */
    public void popupFrame(URL url, String title) {
	getAppletContext().showDocument(url, title);
    }
}
