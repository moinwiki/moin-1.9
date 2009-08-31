/*
 * @(#)Clipboard.java 5.1
 *
 */

package CH.ifa.draw.util;

import java.awt.*;
import java.util.*;

/**
 * A temporary replacement for a global clipboard.
 * It is a singleton that can be used to store and
 * get the contents of the clipboard.
 *
 */
public class Clipboard {
    static Clipboard fgClipboard = new Clipboard();

    /**
     * Gets the clipboard.
     */
    static public Clipboard getClipboard() {
        return fgClipboard;
    }

    private Object fContents;

    private Clipboard() {
    }

    /**
     * Sets the contents of the clipboard.
     */
    public void setContents(Object contents) {
        fContents = contents;
    }

    /**
     * Gets the contents of the clipboard.
     */
    public Object getContents() {
        return fContents;
    }
}
