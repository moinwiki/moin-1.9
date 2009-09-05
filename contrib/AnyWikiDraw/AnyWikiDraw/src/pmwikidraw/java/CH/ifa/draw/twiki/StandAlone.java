package CH.ifa.draw.twiki;

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
import CH.ifa.draw.appframe.*;

public class StandAlone implements Application {
    TWikiFrame frame;

    StandAlone(String[] args) {
	frame = new TWikiFrame(this, null);
	frame.pack();
	frame.show();
    }

    /** Implement Application */
    public void showStatus(String s) {
	//super.showStatus(s);
    }

    /** Implement Application */
    public String getParameter(String name) {
	//return super.getParameter(name);
	return null;
    }

    /** Implement Application */
    public URL getURL(String relURL) throws MalformedURLException {
	//return new URL(getCodeBase(), relURL);
	return null;
    }

    /** Implement Application */
    public void popupFrame(URL url, String title) {
	//getAppletContext().showDocument(url, title);
    }

    public boolean post(
	String url,
	String fileName,
	String type,
	String path,
	String content,
	String comment) {
	return false;
    }

    public static void main(String[] args) {
	StandAlone app = new StandAlone(args);
    }
}
