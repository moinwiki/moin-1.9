/*
 * @(#)FloatingPaletteHandler.java
 *
 * Copyright (c) 1996-2007 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */

package org.jhotdraw.app;

import java.awt.*;
import java.awt.event.*;
import java.util.*;
/**
 * Hides all registered floating palettes, if none of the registered view
 * windows have focus anymore.
 *
 * @author Werner Randelshofer
 * @version $Id: OSXPaletteHandler.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class OSXPaletteHandler {
    private HashSet<Window> palettes = new HashSet<Window>();
    private HashMap<Window,View> windows = new HashMap<Window,View>();
    private static OSXPaletteHandler instance;
    private javax.swing.Timer timer;
    private DefaultOSXApplication app;
    private WindowFocusListener focusHandler = new WindowFocusListener() {
        /**
         * Invoked when the Window is set to be the focused Window, which means
         * that the Window, or one of its subcomponents, will receive keyboard
         * events.
         */
        public void windowGainedFocus(WindowEvent e) {
            timer.stop();
            if (windows.get(e.getWindow()) != null) {
                app.setActiveView((View) windows.get(e.getWindow()));
                showPalettes();
            }
        }
        
        /**
         * Invoked when the Window is no longer the focused Window, which means
         * that keyboard events will no longer be delivered to the Window or any of
         * its subcomponents.
         */
        public void windowLostFocus(WindowEvent e) {
            timer.restart();
        }
    };
    
    /** Creates a new instance. */
    public OSXPaletteHandler(DefaultOSXApplication app) {
        this.app = app;
        timer = new javax.swing.Timer(60, new ActionListener() {
            public void actionPerformed(ActionEvent evt) {
                maybeHidePalettes();
            }
        });
        timer.setRepeats(false);
    }
    
    public void add(Window window, View view) {
        window.addWindowFocusListener(focusHandler);
        windows.put(window, view);
    }
    
    public void remove(Window window) {
        windows.remove(window);
        window.removeWindowFocusListener(focusHandler);
    }
    
    public void addPalette(Window palette) {
        palette.addWindowFocusListener(focusHandler);
        palettes.add(palette);
    }
    
    public void removePalette(Window palette) {
        palettes.remove(palette);
        palette.removeWindowFocusListener(focusHandler);
    }
    
    public Set<Window> getPalettes() {
        return Collections.unmodifiableSet(palettes);
    }
    
    private void showPalettes() {
        for (Window palette : palettes) {
            if (! palette.isVisible()) {
                palette.setVisible(true);
            }
        }
    }
    
    private boolean isFocused(Window w) {
        if (w.isFocused()) return true;
        Window[] ownedWindows = w.getOwnedWindows();
        for (int i=0; i < ownedWindows.length; i++) {
            if (isFocused(ownedWindows[i])) {
                return true;
            }
        }
        return false;
    }
    private void maybeHidePalettes() {
        boolean hasFocus = false;
        for (Window window : windows.keySet()) {
            if (isFocused(window)) {
                hasFocus = true;
                break;
            }
        }
        if (! hasFocus && windows.size() > 0) {
            for (Window palette : palettes) {
                if (isFocused(palette)) {
                    hasFocus = true;
                    break;
                }
            }
        }
        if (! hasFocus) {
            for (Window palette : palettes) {
                palette.setVisible(false);
            }
        }
    }

    public void addWindow(Window window) {
        window.addWindowFocusListener(focusHandler);
        windows.put(window, null);
    }
    public void removeWindow(Window window) {
        windows.remove(window);
        window.removeWindowFocusListener(focusHandler);
    }
}
