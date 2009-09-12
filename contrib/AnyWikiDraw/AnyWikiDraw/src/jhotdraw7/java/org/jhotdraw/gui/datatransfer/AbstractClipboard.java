/*
 * @(#)AbstractClipboard.java
 * 
 * Copyright (c) 2009 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 * 
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */
package org.jhotdraw.gui.datatransfer;

import java.awt.datatransfer.Clipboard;
import java.awt.datatransfer.Transferable;

/**
 * {@code AbstractClipboard} is a wrapper for the system clipboard which
 * can be either the Java AWT Clipboard, the javax.jnlp.AbstractClipboard or
 * native JNI code.
 *
 * @author Werner Randelshofer
 * @version $Id$
 */
public abstract class AbstractClipboard extends Clipboard {

    public AbstractClipboard() {
        super("Clipboard Proxy");
    }

    /** Returns a {@code Transferable} object representing the current contents
     * of the clipboard. If the clipboard currently has no contents, it returns
     * null.
     *
     *    @return The current {@code Transferable} object on the clipboard.
     */
    public abstract Transferable getContents();

    /** Sets the current contents of the clipboard to the specified
     * {@code Transferable} object.
     *
     * @param contents The {@code Transferable} object representing clipboard
     * content.
     */
    public abstract void setContents(Transferable contents);
}
