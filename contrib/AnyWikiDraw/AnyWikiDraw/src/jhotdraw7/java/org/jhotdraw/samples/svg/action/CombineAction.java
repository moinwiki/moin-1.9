/*
 * @(#)CombinePathsAction.java
 *
 * Copyright (c) 2006-2008 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */
package org.jhotdraw.samples.svg.action;

import org.jhotdraw.draw.*;
import org.jhotdraw.draw.action.*;
import org.jhotdraw.samples.svg.figures.*;
import org.jhotdraw.util.*;
import java.util.*;
import javax.swing.undo.*;

/**
 * CombinePathsAction.
 *
 * @author  Werner Randelshofer
 * @version $Id: CombineAction.java 534 2009-06-13 14:54:19Z rawcoder $
 */
public class CombineAction extends AbstractSelectedAction {

    public final static String ID = "edit.combinePaths";
    private CompositeFigure prototype;
    /**
     * If this variable is true, this action groups figures.
     * If this variable is false, this action ungroups figures.
     */
    private boolean isCombineAction;

    /** Creates a new instance. */
    public CombineAction(DrawingEditor editor) {
        this(editor, new SVGPathFigure(true), true);
    }

    public CombineAction(DrawingEditor editor, SVGPathFigure prototype) {
        this(editor, prototype, true);
    }

    public CombineAction(DrawingEditor editor, SVGPathFigure prototype, boolean isGroupingAction) {
        super(editor);
        this.prototype = prototype;
        this.isCombineAction = isGroupingAction;

        labels = ResourceBundleUtil.getBundle("org.jhotdraw.samples.svg.Labels");
        labels.configureAction(this, ID);
    }

    @Override
    protected void updateEnabledState() {
        if (getView() != null) {
            setEnabled(isCombineAction ? canGroup() : canUngroup());
        } else {
            setEnabled(false);
        }
    }

    protected boolean canGroup() {
        boolean canCombine = getView().getSelectionCount() > 1;
        if (canCombine) {
            for (Figure f : getView().getSelectedFigures()) {
                if (!(f instanceof SVGPathFigure)) {
                    canCombine = false;
                    break;
                }
            }
        }
        return canCombine;
    }

    protected boolean canUngroup() {
        return getView() != null && getView().getSelectionCount() == 1 &&
                prototype != null &&
                getView().getSelectedFigures().iterator().next().getClass().equals(
                prototype.getClass()) &&
                ((CompositeFigure) getView().getSelectedFigures().iterator().next()).getChildCount() > 1;
    }

    public void actionPerformed(java.awt.event.ActionEvent e) {
        if (isCombineAction) {
            combineActionPerformed(e);
        } else {
            splitActionPerformed(e);
        }
    }

    public void combineActionPerformed(java.awt.event.ActionEvent e) {
        final DrawingView view = getView();
        Drawing drawing = view.getDrawing();
        if (canGroup()) {
            final List<Figure> ungroupedPaths = drawing.sort(view.getSelectedFigures());
            final int[] ungroupedPathsIndices = new int[ungroupedPaths.size()];
            final int[] ungroupedPathsChildCounts = new int[ungroupedPaths.size()];

            int i = 0;
            for (Figure f : ungroupedPaths) {
                ungroupedPathsIndices[i] = drawing.indexOf(f);
                ungroupedPathsChildCounts[i] = ((CompositeFigure) f).getChildCount();
                //System.out.print("CombineAction indices[" + i + "] = " + ungroupedPathsIndices[i]);
                //System.out.println(" childCount[" + i + "] = " + ungroupedPathsChildCounts[i]);
                i++;
            }
            final CompositeFigure group = (CompositeFigure) prototype.clone();
            combinePaths(view, group, ungroupedPaths, ungroupedPathsIndices[0]);
            UndoableEdit edit = new AbstractUndoableEdit() {

                @Override
                public String getPresentationName() {
                    return labels.getTextProperty("edit.combinePaths");
                }

                @Override
                public void redo() throws CannotRedoException {
                    super.redo();
                    combinePaths(view, group, ungroupedPaths, ungroupedPathsIndices[0]);
                }

                @Override
                public void undo() throws CannotUndoException {
                    super.undo();
                    splitPath(view, group, ungroupedPaths, ungroupedPathsIndices, ungroupedPathsChildCounts);
                }

                @Override
                public boolean addEdit(UndoableEdit anEdit) {
                    return super.addEdit(anEdit);
                }
            };
            fireUndoableEditHappened(edit);
        }
    }

    @SuppressWarnings("unchecked")
    public void splitActionPerformed(java.awt.event.ActionEvent e) {
        final DrawingView view = getView();
        Drawing drawing = view.getDrawing();
        if (canUngroup()) {
            final CompositeFigure group = (CompositeFigure) view.getSelectedFigures().iterator().next();
            final LinkedList<Figure> ungroupedPaths = new LinkedList<Figure>();
            final int[] ungroupedPathsIndices = new int[group.getChildCount()];
            final int[] ungroupedPathsChildCounts = new int[group.getChildCount()];
            int i = 0;
            int index = drawing.indexOf(group);
            for (Figure f : group.getChildren()) {
                SVGPathFigure path = new SVGPathFigure(true);
                for (Map.Entry<AttributeKey, Object> entry : group.getAttributes().entrySet()) {
                    path.setAttribute(entry.getKey(), entry.getValue());
                }
                ungroupedPaths.add(path);
                ungroupedPathsIndices[i] = index + i;
                ungroupedPathsChildCounts[i] = 1;
                i++;
            }
            splitPath(view, group, ungroupedPaths, ungroupedPathsIndices, ungroupedPathsChildCounts);
            UndoableEdit edit = new AbstractUndoableEdit() {

                @Override
                public String getPresentationName() {
                    return labels.getTextProperty("edit.splitPath");
                }

                @Override
                public void redo() throws CannotRedoException {
                    super.redo();
                    splitPath(view, group, ungroupedPaths, ungroupedPathsIndices, ungroupedPathsChildCounts);
                }

                @Override
                public void undo() throws CannotUndoException {
                    super.undo();
                    combinePaths(view, group, ungroupedPaths, ungroupedPathsIndices[0]);
                }
            };
            fireUndoableEditHappened(edit);
        }
    }

    public void splitPath(DrawingView view, CompositeFigure group, List<Figure> ungroupedPaths, int[] ungroupedPathsIndices, int[] ungroupedPathsChildCounts) {
        view.clearSelection();
        Iterator<Figure> groupedFigures = new LinkedList<Figure>(group.getChildren()).iterator();
        group.basicRemoveAllChildren();
        view.getDrawing().remove(group);
        for (int i = 0; i < ungroupedPaths.size(); i++) {
            CompositeFigure path = (CompositeFigure) ungroupedPaths.get(i);
            view.getDrawing().add(ungroupedPathsIndices[i], path);
            path.willChange();
            for (int j = 0; j < ungroupedPathsChildCounts[i]; j++) {
                path.basicAdd(groupedFigures.next());
            }
            path.changed();
        }
        view.addToSelection(ungroupedPaths);
    }

    @SuppressWarnings("unchecked")
    public void combinePaths(DrawingView view, CompositeFigure group, Collection<Figure> figures, int groupIndex) {
        view.getDrawing().basicRemoveAll(figures);
        view.clearSelection();
        view.getDrawing().add(groupIndex, group);
        group.willChange();
        group.basicRemoveAllChildren();
        for (Map.Entry<AttributeKey, Object> entry : figures.iterator().next().getAttributes().entrySet()) {
            group.setAttribute(entry.getKey(), entry.getValue());
        }

        for (Figure f : figures) {
            SVGPathFigure path = (SVGPathFigure) f;
            List<Figure> children = new LinkedList<Figure>(path.getChildren());
            path.basicRemoveAllChildren();
            for (Figure child : children) {
                SVGBezierFigure bez = (SVGBezierFigure) child;
                bez.flattenTransform();
                group.basicAdd(child);
            }

        }
        group.changed();
        view.addToSelection(group);
    }
}
