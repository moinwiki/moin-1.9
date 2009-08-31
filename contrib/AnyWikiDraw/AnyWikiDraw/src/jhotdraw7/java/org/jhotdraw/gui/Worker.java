/*
 * @(#)Worker.java
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
package org.jhotdraw.gui;

import javax.swing.SwingUtilities;

/**
 * This is an abstract class that you subclass to
 * perform GUI-related work in a dedicated event dispatcher.
 * <p>
 * This class is similar to SwingWorker but less complex.
 * Like a SwingWorker it can run using an an internal
 * worker thread but it can also be like a Runnable object.
 *
 * @author Werner Randelshofer
 * @version $Id: Worker.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public abstract class Worker implements Runnable {
    private Object value;  // see getValue(), setValue()
    
    /**
     * Calls #construct on the current thread and invokes
     * #finished on the AWT event dispatcher thread.
     */
    public final void run() {
        final Runnable doFinished = new Runnable() {
            public void run() { 
                finished(getValue()); 
            }
        };
        try {
            setValue(construct());
        } catch (Throwable e) {
            e.printStackTrace();
        } finally {
            SwingUtilities.invokeLater(doFinished);
        }
    }
    
    /**
     * Compute the value to be returned by the <code>get</code> method.
     */
    public abstract Object construct();
    /**
     * Called on the event dispatching thread (not on the worker thread)
     * after the <code>construct</code> method has returned.
     *
     * @param value The return value of the construct method.
     */
    public abstract void finished(Object value);
    /**
     * Get the value produced by the worker thread, or null if it
     * hasn't been constructed yet.
     */
    protected synchronized Object getValue() {
        return value;
    }
    /**
     * Set the value produced by worker thread
     */
    private synchronized void setValue(Object x) {
        value = x;
    }
    
    /**
     * Starts the Worker on an internal worker thread.
     */
    public void start() {
        new Thread(this).start();
    }
}