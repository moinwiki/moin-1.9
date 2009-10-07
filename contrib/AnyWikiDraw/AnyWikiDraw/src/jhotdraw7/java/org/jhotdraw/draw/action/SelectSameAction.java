/*
 * @(#)SelectSameAction.java
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

import org.jhotdraw.draw.DrawingEditor;
import org.jhotdraw.draw.Figure;
import java.util.*;

/**
 * SelectSameAction.
 *
 * @author  Werner Randelshofer
 * @version $Id: SelectSameAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class SelectSameAction extends AbstractSelectedAction {
    public final static String ID = "edit.selectSame";
    /** Creates a new instance. */
    public SelectSameAction(DrawingEditor editor) {
        super(editor);
        labels.configureAction(this, ID);
    }
    
    public void actionPerformed(java.awt.event.ActionEvent e) {
        selectSame();
    }
    
    public void selectSame() {
        HashSet<Class> selectedClasses = new HashSet<Class>();
        for (Figure selected : getView().getSelectedFigures()) {
            selectedClasses.add(selected.getClass());
        }
        for (Figure f : getDrawing().getChildren()) {
            if (selectedClasses.contains(f.getClass())) {
                getView().addToSelection(f);
            }
        }
    }
}
