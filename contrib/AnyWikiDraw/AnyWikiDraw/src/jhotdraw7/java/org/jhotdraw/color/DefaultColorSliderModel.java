/**
 * @(#)DefaultColorSliderModel.java
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
import java.util.LinkedList;
import javax.swing.*;
import javax.swing.event.*;

/**
 * DefaultColorSliderModel.
 *
 * @author Werner Randelshofer
 * @version $Id: DefaultColorSliderModel.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class DefaultColorSliderModel extends AbstractColorSlidersModel {

    protected ColorSystem system;
    /**
     * JSlider's associated to this AbstractColorSystem.
     */
    protected LinkedList<JSlider> sliders = new LinkedList<JSlider>();
    /**
     * Components of the color model.
     */
    protected DefaultBoundedRangeModel[] componentModels;

    public DefaultColorSliderModel() {
        setColorSystem(new HSLRGBColorSystem());
    }
    public DefaultColorSliderModel(ColorSystem sys) {
        setColorSystem(sys);
    }


    public void setColorSystem(ColorSystem newValue) {
        ColorSystem oldValue = system;
        system = newValue;
        componentModels = new DefaultBoundedRangeModel[system.getComponentCount()];

        for (int i = 0; i < componentModels.length; i++) {
            componentModels[i] = new DefaultBoundedRangeModel();
            final int componentIndex = i;
            componentModels[i].addChangeListener(
                    new ChangeListener() {

                        public void stateChanged(ChangeEvent e) {
                            fireColorChanged(componentIndex);
                            fireStateChanged();
                        }
                    });
        }
    }

    /**
     * Configures a JSlider for this AbstractColorSystem.
     * If the JSlider is already configured for another AbstractColorSystem,
     * it is unconfigured first.
     */
    public void configureSlider(int componentIndex, JSlider slider) {
        if (slider.getClientProperty("colorSliderModel") != null) {
            ((DefaultColorSliderModel) slider.getClientProperty("colorSliderModel")).unconfigureSlider(slider);
        }
        if (!(slider.getUI() instanceof ColorSliderUI)) {
            slider.setUI((ColorSliderUI) ColorSliderUI.createUI(slider));
        }
        slider.setModel(getBoundedRangeModel(componentIndex));
        slider.putClientProperty("colorSliderModel", this);
        slider.putClientProperty("colorComponentIndex", new Integer(componentIndex));
        addColorSlider(slider);
    }

    /**
     * Unconfigures a JSlider from this AbstractColorSystem.
     */
    public void unconfigureSlider(JSlider slider) {
        if (slider.getClientProperty("colorSliderModel") == this) {
            // XXX - This creates a NullPointerException ??
            //slider.setUI((SliderUI) UIManager.getUI(slider));
            slider.setModel(new DefaultBoundedRangeModel());
            slider.putClientProperty("colorSliderModel", null);
            slider.putClientProperty("colorComponentIndex", null);
            removeColorSlider(slider);
        }
    }

    /**
     * Returns the bounded range model of the specified color componentIndex.
     */
    public DefaultBoundedRangeModel getBoundedRangeModel(int componentIndex) {
        return componentModels[componentIndex];
    }

    /**
     * Returns the value of the specified color componentIndex.
     */
    public int getSliderValue(int componentIndex) {
        return componentModels[componentIndex].getValue();
    }

    /**
     * Sets the value of the specified color componentIndex.
     */
    public void setSliderValue(int componentIndex, int value) {
        componentModels[componentIndex].setValue(value);
    }

    protected void addColorSlider(JSlider slider) {
        sliders.add(slider);
    }

    protected void removeColorSlider(JSlider slider) {
        sliders.remove(slider);
    }

    protected void fireColorChanged(int componentIndex) {
        Integer index = new Integer(componentIndex);
        CompositeColor value = getCompositeColor();
        for (JSlider slider : sliders) {
            slider.putClientProperty("colorComponentChange", index);
            slider.putClientProperty("colorComponentValue", value);
        }
    }

    public ColorSystem getColorSystem() {
        return system;
    }

    public int getComponentCount() {
        return system.getComponentCount();
    }

    public CompositeColor getCompositeColor() {
        float[] c = new float[system.getComponentCount()];
        int i = 0;
        for (DefaultBoundedRangeModel m : componentModels) {
            c[i] = (m.getValue() - m.getMinimum()) /
                    (float) (m.getMaximum() - m.getMinimum());
            i++;
        }
        return new CompositeColor(system, c);
    }

    public int getInterpolatedRGB(int componentIndex, float componentValue) {
        float[] c = new float[system.getComponentCount()];
        int i = 0;
        for (DefaultBoundedRangeModel m : componentModels) {
            c[i] = (m.getValue() - m.getMinimum()) /
                    (float) (m.getMaximum() - m.getMinimum());
            i++;
        }
        c[componentIndex] = componentValue;
        return system.toRGB(c);
    }

    public void setComponentValue(int componentIndex, float newValue) {
       BoundedRangeModel brm = componentModels[componentIndex];
       brm.setValue((int) ((brm.getMaximum() - brm.getMinimum()) * newValue) + brm.getMinimum());
    }

    public float getComponentValue(int componentIndex) {
       BoundedRangeModel brm = componentModels[componentIndex];
       return (brm.getValue() - brm.getMinimum()) / (float) (brm.getMaximum() - brm.getMinimum());
    }

    public void setCompositeColor(CompositeColor newValue) {
        float[] c = newValue.getComponents();
        int i = 0;
        for (DefaultBoundedRangeModel m : componentModels) {
            m.setValue((int) (c[i] * (m.getMaximum() - m.getMinimum() + m.getMinimum())));
            i++;
        }
    }

    public Color getColor() {
        return getCompositeColor().getColor();
    }

    public void setColor(Color newValue) {
        setCompositeColor(new CompositeColor(system, newValue));
    }
}
