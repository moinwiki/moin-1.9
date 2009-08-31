/*
 * @(#)BoundedRangeModel.java
 *
 * Copyright (c) 1999-2008 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */
//package ch.randelshofer.io;
package org.jhotdraw.io;

import java.awt.event.*;
import javax.swing.event.*;
import javax.swing.BoundedRangeModel;
import java.io.*;
/**
 * This input stream implements the BoundedRangeModel and allows
 * the observation of the input reading process.
 *
 * @author  Werner Randelshofer, Staldenmattweg 2, CH-6405 Immensee, Switzerland.
 * @version $Id: BoundedRangeInputStream.java 527 2009-06-07 14:28:19Z rawcoder $
 * <br>history  1.0.1  02.05.1999  #setMaximum overrides the size information
 * from the file.
 * <br>history  1.0   20.03.1999  Derived from javax.swing.ProgressMonitorInputStream.
 */
public class BoundedRangeInputStream
extends FilterInputStream
implements BoundedRangeModel {
    private int nread_ = 0;
    private int size_ = 0;
    private boolean valueIsAdjusting_;
    
    /**
     * Only one ChangeEvent is needed per model instance since the
     * event's only (read-only) state is the source property.  The source
     * of events generated here is always "this".
     */
    protected transient ChangeEvent changeEvent_ = null;
    
    /** The listeners waiting for model changes. */
    protected EventListenerList listenerList_ = new EventListenerList();
    
    /**
     * Create a new instance.
     */
    public BoundedRangeInputStream(InputStream in) {
        super(in);
        try
        { size_ = in.available(); }
        catch(IOException ioe)
        { size_ = 0; }
    }
    
    /**
     * Overrides <code>FilterInputStream.read</code>
     * to update the value after the read.
     */
    public int read()
    throws IOException {
        int c = in.read();
        if (c >=0)
        { incrementValue(1); }
        return c;
    }
    /**
     * Overrides <code>FilterInputStream.read</code>
     * to update the value after the read.
     */
    public int read(byte b[])
    throws IOException {
        int nr = in.read(b);
        incrementValue(nr);
        return nr;
    }
    
    /**
     * Overrides <code>FilterInputStream.read</code>
     * to update the value after the read.
     */
    public int read(byte b[],int off,int len)
    throws IOException {
        int nr = in.read(b, off, len);
        incrementValue(nr);
        return nr;
    }
    /**
     * Overrides <code>FilterInputStream.skip</code>
     * to update the value after the skip.
     */
    public long skip(long n) throws IOException {
        long nr = in.skip(n);
        incrementValue( (int)nr);
        return nr;
    }
    /**
     * Overrides <code>FilterInputStream.reset</code>
     * to reset the progress monitor as well as the stream.
     */
    public synchronized void reset()
    throws IOException {
        in.reset();
        nread_ = size_-in.available();
        fireStateChanged();
    }
    /**
     * Increments the extent by the indicated value.
     * Negative Increments are ignored.
     *
     * @param  inc  The incrementValue value.
     */
    private void incrementValue(int inc) {
        if (inc > 0) {
            nread_+=inc;
            if (nread_ > size_)
            { size_ = nread_; }
            fireStateChanged();
        }
    }
    /**
     * Returns the minimum acceptable value.
     *
     * @return the value of the minimum property
     * @see #setMinimum
     */
    public int getMinimum()
    { return 0; }
    
    
    /**
     * Ignored: The minimum of an input stream is always zero.
     *
     * Sets the model's minimum to <I>newMinimum</I>.   The
     * other three properties may be changed as well, to ensure
     * that:
     * <pre>
     * minimum <= value <= value+extent <= maximum
     * </pre>
     * <p>
     * Notifies any listeners if the model changes.
     *
     * @param newMinimum the model's new minimum
     * @see #getMinimum
     * @see #addChangeListener
     */
    public void setMinimum(int newMinimum) {}
    
    
    /**
     * Returns the model's maximum.  Note that the upper
     * limit on the model's value is (maximum - extent).
     *
     * @return the value of the maximum property.
     * @see #setMaximum
     * @see #setExtent
     */
    public int getMaximum() { return size_; }
    
    
    /**
     * Ignored: The maximum of an input stream can not be changed.
     * #
     * Sets the model's maximum to <I>newMaximum</I>. The other
     * three properties may be changed as well, to ensure that
     * <pre>
     * minimum <= value <= value+extent <= maximum
     * </pre>
     * <p>
     * Notifies any listeners if the model changes.
     *
     * @param newMaximum the model's new maximum
     * @see #getMaximum
     * @see #addChangeListener
     */
    public void setMaximum(int newMaximum) {
        size_ = newMaximum;
        fireStateChanged();
    }
    
    
    /**
     * Returns the current read position.
     *
     * Returns the model's current value.  Note that the upper
     * limit on the model's value is <code>maximum - extent</code>
     * and the lower limit is <code>minimum</code>.
     *
     * @return  the model's value
     * @see     #setValue
     */
    public int getValue() { return nread_; }
    
    
    /**
     * Ignored: The value is always zero.
     *
     * Sets the model's current value to <code>newValue</code> if <code>newValue</code>
     * satisfies the model's constraints. Those constraints are:
     * <pre>
     * minimum <= value <= value+extent <= maximum
     * </pre>
     * Otherwise, if <code>newValue</code> is less than <code>minimum</code>
     * it's set to <code>minimum</code>, if its greater than
     * <code>maximum</code> then it's set to <code>maximum</code>, and
     * if it's greater than <code>value+extent</code> then it's set to
     * <code>value+extent</code>.
     * <p>
     * When a BoundedRange model is used with a scrollbar the value
     * specifies the origin of the scrollbar knob (aka the "thumb" or
     * "elevator").  The value usually represents the origin of the
     * visible part of the object being scrolled.
     * <p>
     * Notifies any listeners if the model changes.
     *
     * @param newValue the model's new value
     * @see #getValue
     */
    public void setValue(int newValue) {}
    
    
    /**
     * This attribute indicates that any upcoming changes to the value
     * of the model should be considered a single event. This attribute
     * will be set to true at the start of a series of changes to the value,
     * and will be set to false when the value has finished changing.  Normally
     * this allows a listener to only take action when the final value change in
     * committed, instead of having to do updates for all intermediate values.
     * <p>
     * Sliders and scrollbars use this property when a drag is underway.
     *
     * @param b true if the upcoming changes to the value property are part of a series
     */
    public void setValueIsAdjusting(boolean b)
    { valueIsAdjusting_ = b; }
    
    
    /**
     * Returns true if the current changes to the value property are part
     * of a series of changes.
     *
     * @return the valueIsAdjustingProperty.
     * @see #setValueIsAdjusting
     */
    public boolean getValueIsAdjusting()
    { return valueIsAdjusting_; }
    
    
    /**
     * Returns the model's extent, the length of the inner range that
     * begins at the model's value.
     *
     * @return  the value of the model's extent property
     * @see     #setExtent
     * @see     #setValue
     */
    public int getExtent() { return 0; }
    
    
    /**
     * Ignored: The extent is always zero.
     */
    public void setExtent(int newExtent)
    { }
    
    
    
    /**
     * Ignored: All values depend on the input stream.
     */
    public void setRangeProperties(int value, int extent, int min, int max, boolean adjusting)
    {}
    
    
    
    /**
     * Adds a ChangeListener to the model's listener list.
     *
     * @param l the ChangeListener to add
     * @see #removeChangeListener
     */
    public void addChangeListener(ChangeListener l) {
        listenerList_.add(ChangeListener.class, l);
    }
    
    
    /**
     * Removes a ChangeListener.
     *
     * @param l the ChangeListener to remove
     * @see #addChangeListener
     * @see BoundedRangeModel#removeChangeListener
     */
    public void removeChangeListener(ChangeListener l) {
        listenerList_.remove(ChangeListener.class, l);
    }
    
    
    /**
     * Run each ChangeListeners stateChanged() method.
     *
     * @see #setRangeProperties
     * @see EventListenerList
     */
    protected void fireStateChanged() {
        Object[] listeners = listenerList_.getListenerList();
        for (int i = listeners.length - 2; i >= 0; i -=2 ) {
            if (listeners[i] == ChangeListener.class) {
                if (changeEvent_ == null) {
                    changeEvent_ = new ChangeEvent(this);
                }
                ((ChangeListener)listeners[i+1]).stateChanged(changeEvent_);
            }
        }
    }
}
