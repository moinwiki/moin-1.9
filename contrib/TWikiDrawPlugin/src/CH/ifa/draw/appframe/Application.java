package CH.ifa.draw.appframe;

import java.net.URL;
import java.net.MalformedURLException;
import java.io.IOException;

/**
 * Interface to controlling application, either an applet or a java
 * application. Makes a DrawFrame independent of it's context.
 */
public interface Application {
    /** Show status string, eg in applet area */
    void showStatus(String s);
    /** Get command-line or applet parameter */
    String getParameter(String name);
    /** Get URL relative to the codebase of the app */
    URL getURL(String relURL) throws MalformedURLException;
    /** Popup a URL in a new frame */
    void popupFrame(URL url, String title);
}
