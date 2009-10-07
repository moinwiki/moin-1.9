/*
 * @(#)SplitPathsAction.java
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
package org.jhotdraw.samples.odg.action;

import org.jhotdraw.draw.*;
import org.jhotdraw.draw.action.*;
import org.jhotdraw.samples.odg.figures.*;
import org.jhotdraw.undo.*;
import org.jhotdraw.util.*;
import java.util.*;
import javax.swing.*;
import javax.swing.undo.*;

/**
 * SplitPathsAction.
 *
 * @author  Werner Randelshofer
 * @version $Id: SplitAction.java 534 2009-06-13 14:54:19Z rawcoder $
 */
public class SplitAction extends UngroupAction {

    public final static String ID = "edit.splitPath";

    /** Creates a new instance. */
    public SplitAction(DrawingEditor editor) {
        super(editor, new ODGPathFigure());

        labels = ResourceBundleUtil.getBundle("org.jhotdraw.samples.odg.Labels");
        labels.configureAction(this, ID);
    }

    protected boolean canUngroup() {
        if (super.canUngroup()) {
            return ((CompositeFigure) getView().getSelectedFigures().iterator().next()).getChildCount() > 1;
        }
        return false;
    }

    @SuppressWarnings("unchecked")
    @Override
    public Collection<Figure> ungroupFigures(DrawingView view, CompositeFigure group) {
        LinkedList<Figure> figures = new LinkedList<Figure>(group.getChildren());
        view.clearSelection();
        group.basicRemoveAllChildren();
        LinkedList<Figure> paths = new LinkedList<Figure>();
        for (Figure f : figures) {
            ODGPathFigure path = new ODGPathFigure();
            path.removeAllChildren();
            for (Map.Entry<AttributeKey, Object> entry : group.getAttributes().entrySet()) {
                path.setAttribute(entry.getKey(), entry.getValue());
            }
            path.add(f);
            view.getDrawing().basicAdd(path);
            paths.add(path);
        }
        view.getDrawing().remove(group);
        view.addToSelection(paths);
        return figures;
    }

    @SuppressWarnings("unchecked")
    @Override
    public void groupFigures(DrawingView view, CompositeFigure group, Collection<Figure> figures) {
        Collection<Figure> sorted = view.getDrawing().sort(figures);
        view.getDrawing().basicRemoveAll(figures);
        view.clearSelection();
        view.getDrawing().add(group);
        group.willChange();
        ((ODGPathFigure) group).removeAllChildren();
        for (Map.Entry<AttributeKey, Object> entry : figures.iterator().next().getAttributes().entrySet()) {
            group.setAttribute(entry.getKey(), entry.getValue());
        }
        for (Figure f : sorted) {
            ODGPathFigure path = (ODGPathFigure) f;
            for (Figure child : path.getChildren()) {
                group.basicAdd(child);
            }
        }
        group.changed();
        view.addToSelection(group);
    }
}
