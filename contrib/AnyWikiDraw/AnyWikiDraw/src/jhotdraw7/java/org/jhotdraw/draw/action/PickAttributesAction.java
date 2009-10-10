/*
 * @(#)PickAttributesAction.java
 *
 * Copyright (c) 1996-2006 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */

package org.jhotdraw.draw.action;

import org.jhotdraw.util.*;
import java.util.*;
import org.jhotdraw.draw.*;
import static org.jhotdraw.draw.AttributeKeys.*;
/**
 * PickAttributesAction.
 *
 * @author Werner Randelshofer
 * @version $Id: PickAttributesAction.java 534 2009-06-13 14:54:19Z rawcoder $
 */
public class PickAttributesAction extends AbstractSelectedAction {
    private ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.draw.Labels");
    
    private Set<AttributeKey> excludedAttributes = new HashSet<AttributeKey>(
            Arrays.asList(new AttributeKey[] { TRANSFORM, TEXT }));
    
    /** Creates a new instance. */
    public PickAttributesAction(DrawingEditor editor) {
        super(editor);
        labels.configureAction(this, "edit.pickAttributes");
        setEnabled(true);
    }
    
    /**
     * Set of attributes that is excluded when applying default attributes.
     * By default, the TRANSFORM attribute is excluded.
     */
    public void setExcludedAttributes(Set<AttributeKey> a) {
        this.excludedAttributes = a;
    }
    
    public void actionPerformed(java.awt.event.ActionEvent e) {
        pickAttributes();
    }
    
    @SuppressWarnings("unchecked")
    public void pickAttributes() {
        DrawingEditor editor = getEditor();
        Collection<Figure> selection = getView().getSelectedFigures();
        if (selection.size() > 0) {
            Figure figure = (Figure) selection.iterator().next();
            for (Map.Entry<AttributeKey, Object> entry : figure.getAttributes().entrySet()) {
                if (! excludedAttributes.contains(entry.getKey())) {
                    editor.setDefaultAttribute(entry.getKey(), entry.getValue());
                }
            }
        }
    }
    public void selectionChanged(FigureSelectionEvent evt) {
        setEnabled(getView().getSelectionCount() == 1);
    }
}
