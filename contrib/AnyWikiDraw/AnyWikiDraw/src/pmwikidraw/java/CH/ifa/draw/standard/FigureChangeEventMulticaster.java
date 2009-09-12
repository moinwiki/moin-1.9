/*
 * @(#)FigureChangeEventMulticaster.java 5.1
 *
 */

package CH.ifa.draw.standard;

import CH.ifa.draw.util.*;
import CH.ifa.draw.framework.*;
import java.awt.*;
import java.awt.event.*;
import java.util.*;
import java.io.*;

/**
 * Manages a list of FigureChangeListeners to be notified of
 * specific FigureChangeEvents.
 */


public class FigureChangeEventMulticaster extends
    AWTEventMulticaster implements FigureChangeListener {

    public FigureChangeEventMulticaster(EventListener a, EventListener b) {
    	super(a, b);
    }

    public void figureInvalidated(FigureChangeEvent e) {
        ((FigureChangeListener)a).figureInvalidated(e);
        ((FigureChangeListener)b).figureInvalidated(e);
    }

    public void figureRequestRemove(FigureChangeEvent e) {
        ((FigureChangeListener)a).figureRequestRemove(e);
        ((FigureChangeListener)b).figureRequestRemove(e);
    }

    public void figureRequestUpdate(FigureChangeEvent e) {
        ((FigureChangeListener)a).figureRequestUpdate(e);
        ((FigureChangeListener)b).figureRequestUpdate(e);
    }

    public void figureChanged(FigureChangeEvent e) {
        ((FigureChangeListener)a).figureChanged(e);
        ((FigureChangeListener)b).figureChanged(e);
    }

    public void figureRemoved(FigureChangeEvent e) {
        ((FigureChangeListener)a).figureRemoved(e);
        ((FigureChangeListener)b).figureRemoved(e);
    }

    public static FigureChangeListener add(FigureChangeListener a, FigureChangeListener b) {
        return (FigureChangeListener)addInternal(a, b);
    }


    public static FigureChangeListener remove(FigureChangeListener l, FigureChangeListener oldl) {
	    return (FigureChangeListener) removeInternal(l, oldl);
    }

    protected EventListener remove(EventListener oldl)
    {
        if (oldl == a)
            return b;
        if (oldl == b)
            return a;
        EventListener a2 = removeInternal((FigureChangeListener)a, oldl);
        EventListener b2 = removeInternal((FigureChangeListener)b, oldl);
        if (a2 == a && b2 == b)
            return this;
        else
            return addInternal((FigureChangeListener)a2, (FigureChangeListener)b2);
    }

    protected static EventListener addInternal(FigureChangeListener a, FigureChangeListener b) {
	    if (a == null)  return b;
	    if (b == null)  return a;
	    return new FigureChangeEventMulticaster(a, b);
    }

    protected static EventListener removeInternal(EventListener l, EventListener oldl) {
    	if (l == oldl || l == null) {
    	    return null;
    	} else if (l instanceof FigureChangeEventMulticaster) {
    	    return ((FigureChangeEventMulticaster)l).remove(oldl);
    	} else {
    	    return l;		// it's not here
    	}
    }

}
