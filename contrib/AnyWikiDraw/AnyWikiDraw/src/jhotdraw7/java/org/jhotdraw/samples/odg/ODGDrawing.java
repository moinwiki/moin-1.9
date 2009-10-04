/*
 * @(#)ODGDrawing.java
 *
 * Copyright (c) 2007 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */

package org.jhotdraw.samples.odg;

import java.io.IOException;
import org.jhotdraw.draw.*;
import org.jhotdraw.samples.svg.figures.*;
import org.jhotdraw.xml.*;
/**
 * ODGDrawing.
 * <p>
 * XXX - This class is going away in future versions: We don't need
 * to subclass QuadTreeDrawing for ODG since we can represent all ODG-specific
 * AttributeKey's instead of using JavaBeans properties.
 * 
 * @author Werner Randelshofer
 * @version $Id: ODGDrawing.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class ODGDrawing extends QuadTreeDrawing {
    private String title;
    private String description;
    
    /** Creates a new instance. */
    public ODGDrawing() {
    }
    
    public void setTitle(String newValue) {
        String oldValue = title;
        title = newValue;
        firePropertyChange("title", oldValue, newValue);
    }
    public String getTitle() {
        return title;
    }
    public void setDescription(String newValue) {
        String oldValue = description;
        description = newValue;
        firePropertyChange("description", oldValue, newValue);
    }
    public String getDescription() {
        return description;
    }
    
    
    public void read(DOMInput in) throws IOException {
        for (int i=0, n = in.getElementCount(); i < n; i++) {
            in.openElement(i);
            String name = in.getTagName();
            if (name.equals("title")) {
                title = in.getText();
                in.closeElement();
            } else if (name.equals("desc")) {
                description = in.getText();
                in.closeElement();
            } else if (name.equals("defs")) {
                // We ignore "defs" elements for now.
                in.closeElement();
            } else if (name.equals("use")) {
                // We ignore "use" elements for now.
                in.closeElement();
            } else if (name.equals("script")) {
                // We ignore "script" elements for now.
                in.closeElement();
            } else if (name.equals("style")) {
                // We ignore "style" elements for now.
                in.closeElement();
            } else if (name.equals("radialGradient")) {
                // We ignore "radialGradient" elements for now.
                in.closeElement();
            } else {
                in.closeElement();
                Object f = (Object) in.readObject(i);
                if (f instanceof ODGDrawing) {
                    SVGGroupFigure g = new SVGGroupFigure();
                    g.willChange();
                    for (Figure child : ((ODGDrawing) f).getChildren()) {
                        g.basicAdd(child);
                    }
                    g.changed();
                    if (! g.isEmpty()) {
                        add(g);
                    }
                } else if (f instanceof SVGFigure) {
                    if (!((SVGFigure) f).isEmpty()) {
                        add((Figure) f);
                    }
                } else {
                    throw new IOException("Unexpected child "+f);
                }
            }
        }
        readAttributes(in);
    }
    
    protected void readAttributes(DOMInput in) throws IOException {
        // SVGUtil.readAttributes(this, in);
    }
    
   @Override public void write(DOMOutput out) throws IOException {
        out.addAttribute("xmlns","http://www.w3.org/2000/svg");
        out.addAttribute("version","1.2");
        out.addAttribute("baseProfile","tiny");

       for (Figure f : getChildren()) {
            out.writeObject(f);
        }
    }
}
