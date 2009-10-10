/*
 * @(#)AWTClipboard.java
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
 * {@code AWTClipboard} acts as a proxy to an AWT {@code Clipboard} object.
 *
 * <hr>
 * <b>Design Patterns</b>
 *
 * <p><em>Proxy</em><br>
 * {@code AWTClipboard} acts as a proxy to an AWT {@code Clipboard} object.<br>
 * Proxy: {@link AWTClipboard}; Target: {@code java.awt.datatransfer.Clipboard}.
 * </hr>
 *
 * @author Werner Randelshofer
 * @version $Id$
 */
public class AWTClipboard extends AbstractClipboard {
    /** The proxy target. */
    private Clipboard target;

    /**
     * Creates a new proxy for the specified target object.
     *
     * @param target A Clipboard object.
     */
    public AWTClipboard(Clipboard target) {
        this.target = target;
    }

    /** Returns the proxy target. */
    public Clipboard getTarget() {
        return target;
    }

    public Transferable getContents() {
        return target.getContents(this);
    }

    public void setContents(Transferable contents) {
        target.setContents(contents, null);
    }

}
