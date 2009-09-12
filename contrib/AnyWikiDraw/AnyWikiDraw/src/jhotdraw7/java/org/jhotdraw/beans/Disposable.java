/*
 * @(#)Disposable.java
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

package org.jhotdraw.beans;

/**
 * Interface for objects which have a dispose method.
 *
 * @author Werner Randelshofer
 * @version $Id: Disposable.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public interface Disposable {
    /** Disposes of all resources held by this object so that they can be
     * garbage collected.
     */
    public void dispose();
}
