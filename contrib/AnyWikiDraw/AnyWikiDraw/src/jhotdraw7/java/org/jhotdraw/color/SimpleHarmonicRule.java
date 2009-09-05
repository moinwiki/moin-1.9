/**
 * @(#)SimpleHarmonicRule.java
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

/**
 * SimpleHarmonicRule.
 *
 * @author Werner Randelshofer
 * @version $Id: SimpleHarmonicRule.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class SimpleHarmonicRule extends AbstractHarmonicRule {

    private float difference;
    private int componentIndex;

    public SimpleHarmonicRule(int componentIndex, float difference, int baseIndex, int... derivedIndices) {
        this.componentIndex = componentIndex;
        this.difference = difference;
        this.baseIndex = baseIndex;
        this.derivedIndices = derivedIndices;
    }

    public void setConstraint(float constraint) {
        this.difference = constraint;
    }

    public float getConstraint(float constraint) {
        return constraint;
    }

    public void setComponentIndex(int newValue) {
        this.componentIndex = newValue;
    }

    public int getComponentIndex() {
        return componentIndex;
    }

    public void apply(HarmonicColorModel model) {
        if (derivedIndices != null) {
            CompositeColor baseColor = model.get(getBaseIndex());
            if (baseColor != null) {
                float[] derivedComponents = null;
                for (int i = 0; i < derivedIndices.length; i++) {
                    derivedComponents = baseColor.getComponents(derivedComponents);
                    derivedComponents[componentIndex] = baseColor.getComponent(componentIndex) + difference * (i + 1);
                    model.set(derivedIndices[i], new CompositeColor(model.getColorSystem(), derivedComponents));
                }
            }
        }
    }

    public void colorChanged(HarmonicColorModel model, int index, CompositeColor oldValue, CompositeColor newValue) {
        //
    }
}
