/**
 * @(#)AbstractHarmonicRule.java
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
 * AbstractHarmonicRule.
 *
 * @author Werner Randelshofer
 * @version $Id: AbstractHarmonicRule.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public abstract class AbstractHarmonicRule implements HarmonicRule {
    protected int baseIndex;
    protected int[] derivedIndices;
    
    
    public void setBaseIndex() {
        this.baseIndex = baseIndex;
    }

    public int getBaseIndex() {
        return baseIndex;
    }

    public void setDerivedIndices(int... indices) {
        this.derivedIndices = indices;
    }

    public int[] getDerivedIndices() {
        return derivedIndices;
    }

}
