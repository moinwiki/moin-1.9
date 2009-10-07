/**
 * @(#)HarmonicRule.java
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
 * HarmonicRule.
 *
 * @author Werner Randelshofer
 * @version $Id: HarmonicRule.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public interface HarmonicRule {
    
    public void setBaseIndex();
    
    public int getBaseIndex();
    
    public void setDerivedIndices(int... indices);
    
    public int[] getDerivedIndices();
    
    public void apply(HarmonicColorModel model);
    
    public void colorChanged(HarmonicColorModel model, int index, CompositeColor oldValue, CompositeColor newValue);
}
