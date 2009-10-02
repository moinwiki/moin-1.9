/**
 * @(#)DefaultHarmonicColorModel.java
 *
 * Copyright (c) 2008 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */
package org.jhotdraw.color;

import java.awt.Color;
import java.beans.*;
import java.util.ArrayList;
import javax.swing.*;
import static org.jhotdraw.color.HarmonicColorModel.*;

/**
 * DefaultHarmonicColorModel.
 *
 * @author Werner Randelshofer
 * @version $Id: DefaultHarmonicColorModel.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class DefaultHarmonicColorModel extends AbstractListModel implements HarmonicColorModel {

    protected PropertyChangeSupport propertySupport = new PropertyChangeSupport(this);
    private ArrayList<CompositeColor> colors;
    private ColorSliderModel sliderModel;
    private int base;
    private ArrayList<HarmonicRule> rules;
    private float customHueConstraint = 30f / 360f;
    private int adjusting;

    public DefaultHarmonicColorModel() {
        ColorSystem sys = new HSLRYBColorSystem();
        sliderModel = new DefaultColorSliderModel(sys);
        colors = new ArrayList<CompositeColor>();
        rules = new ArrayList<HarmonicRule>();

        base = 0;
        add(new CompositeColor(sys, Color.RED));

        DefaultListModel x;
    }

    public void setSize(int newValue) {
        int oldSize = size();
        while (colors.size() > newValue) {
            colors.remove(colors.size() - 1);
        }
        ColorSystem sys = sliderModel.getColorSystem();
        while (colors.size() < newValue) {
            colors.add(null);
        }

        if (oldSize < newValue) {
            fireIntervalRemoved(this, oldSize, newValue - 1);
        } else if (oldSize > newValue) {
            fireIntervalRemoved(this, newValue, oldSize - 1);
        }
    }

    public int size() {
        return colors.size();
    }

    public boolean isAdjusting() {
        return adjusting > 0;
    }

    public void set(int index, CompositeColor newValue) {
        adjusting++;
        CompositeColor oldValue = colors.set(index, newValue);
        for (HarmonicRule r : rules) {
            r.colorChanged(this, index, oldValue, newValue);
        }
        for (HarmonicRule r : rules) {
            if (r.getBaseIndex() == index) {
                r.apply(this);
            }
        }
        adjusting--;
        fireContentsChanged(this, index, index);
    }
    
    public void applyRules() {
        for (HarmonicRule r : rules) {
            if (r.getBaseIndex() == base) {
                r.apply(this);
            }
        }
    }

    public CompositeColor get(int index) {
        return colors.get(index);
    }

    public boolean add(CompositeColor c) {
        boolean b = colors.add(c);
        if (b) {
            fireIntervalAdded(this, size() - 1, size() - 1);
        }
        return b;
    }

    public void setBase(int newValue) {
        base = newValue;
    }

    public int getBase() {
        return base;
    }

    public float[] RGBtoComponent(int rgb, float[] hsb) {
        return sliderModel.getColorSystem().toComponents(rgb, hsb);
    }

    public int componentToRGB(float h, float s, float b) {
        return sliderModel.getColorSystem().toRGB(h, s, b);
    }

    public int getSize() {
        return size();
    }

    public Object getElementAt(int index) {
        return get(index);
    }

    public ColorSystem getColorSystem() {
        return sliderModel.getColorSystem();
    }

    public void addRule(HarmonicRule newValue) {
        rules.add(newValue);
    }

    public void removeAllRules() {
        rules.clear();
    }

    public void addPropertyChangeListener(PropertyChangeListener listener) {
        propertySupport.addPropertyChangeListener(listener);
    }

    public void addPropertyChangeListener(String propertyName, PropertyChangeListener listener) {
        propertySupport.addPropertyChangeListener(propertyName, listener);
    }

    public void removePropertyChangeListener(PropertyChangeListener listener) {
        propertySupport.removePropertyChangeListener(listener);
    }

    public void removePropertyChangeListener(String propertyName, PropertyChangeListener listener) {
        propertySupport.removePropertyChangeListener(propertyName, listener);
    }

    protected void firePropertyChange(String propertyName, boolean oldValue, boolean newValue) {
        propertySupport.firePropertyChange(propertyName, oldValue, newValue);
    }

    protected void firePropertyChange(String propertyName, int oldValue, int newValue) {
        propertySupport.firePropertyChange(propertyName, oldValue, newValue);
    }

    protected void firePropertyChange(String propertyName, Object oldValue, Object newValue) {
        propertySupport.firePropertyChange(propertyName, oldValue, newValue);
    }

    public DefaultHarmonicColorModel clone() {
        DefaultHarmonicColorModel that;
        try {
            that = (DefaultHarmonicColorModel) super.clone();
        } catch (CloneNotSupportedException ex) {
            InternalError error = new InternalError("Clone failed");
            error.initCause(ex);
            throw error;
        }
        that.propertySupport = new PropertyChangeSupport(that);
        return that;
    }

    public void setColorSystem(ColorSystem newValue) {
        ColorSystem oldValue = sliderModel.getColorSystem();
        sliderModel.setColorSystem(newValue);
        firePropertyChange(COLOR_SYSTEM_PROPERTY, oldValue, newValue);
        for (int i = 0; i < colors.size(); i++) {
            if (get(i) != null) {
                set(i, new CompositeColor(newValue, get(i).getColor()));
            }
        }
        fireContentsChanged(this, 0, size() - 1);
    }
}
