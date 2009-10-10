/*
 * @(#)ODGApplicationModel.java
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

import java.util.*;
import javax.swing.*;
import org.jhotdraw.app.*;

import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.geom.*;
import org.jhotdraw.app.action.*;
import org.jhotdraw.samples.odg.action.*;
import org.jhotdraw.samples.odg.figures.*;
import org.jhotdraw.util.*;
import java.util.*;
import javax.swing.*;
import org.jhotdraw.app.*;
import org.jhotdraw.draw.*;
import org.jhotdraw.draw.action.*;
import static org.jhotdraw.samples.odg.ODGAttributeKeys.*;
/**
 * ODGApplicationModel.
 *
 * @author Werner Randelshofer
 * @version $Id: ODGApplicationModel.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class ODGApplicationModel extends DefaultApplicationModel {
    private final static double[] scaleFactors = {5, 4, 3, 2, 1.5, 1.25, 1, 0.75, 0.5, 0.25, 0.10};
   /**
     * This editor is shared by all views.
     */
    private DefaultDrawingEditor sharedEditor;
    
    
    /** Creates a new instance. */
    public ODGApplicationModel() {
        setViewClass(ODGView.class);
    }
    public DefaultDrawingEditor getSharedEditor() {
        if (sharedEditor == null) {
            sharedEditor = new DefaultDrawingEditor();
        }
        return sharedEditor;
    }
     
    public static Collection<Action> createDrawingActions(DrawingEditor editor) {
        LinkedList<Action> a = new LinkedList<Action>();
        a.add(new CutAction());
        a.add(new CopyAction());
        a.add(new PasteAction());
        a.add(new SelectAllAction());
        a.add(new SelectSameAction(editor));
        
        return a;
    }
    public static Collection<Action> createSelectionActions(DrawingEditor editor) {
        LinkedList<Action> a = new LinkedList<Action>();
        a.add(new DuplicateAction());
        
        a.add(null); // separator
        a.add(new GroupAction(editor, new ODGGroupFigure()));
        a.add(new UngroupAction(editor, new ODGGroupFigure()));
        a.add(new CombineAction(editor));
        a.add(new SplitAction(editor));
        
        a.add(null); // separator
        a.add(new BringToFrontAction(editor));
        a.add(new SendToBackAction(editor));
        
        return a;
    }
    private void addCreationButtonsTo(JToolBar tb, final DrawingEditor editor) {
        // AttributeKeys for the entitie sets
        HashMap<AttributeKey,Object> attributes;
        
        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.samples.odg.Labels");
        ResourceBundleUtil drawLabels = ResourceBundleUtil.getBundle("org.jhotdraw.draw.Labels");
        
        ButtonFactory.addSelectionToolTo(tb, editor, createDrawingActions(editor), createSelectionActions(editor));
        tb.addSeparator();
        
        attributes = new HashMap<AttributeKey,Object>();
        ButtonFactory.addToolTo(tb, editor, new CreationTool(new ODGRectFigure(), attributes), "edit.createRectangle", drawLabels);
        attributes = new HashMap<AttributeKey,Object>();
        attributes.put(AttributeKeys.FILL_COLOR, null);
        attributes.put(AttributeKeys.STROKE_COLOR, Color.black);
        ButtonFactory.addToolTo(tb, editor, new CreationTool(new ODGPathFigure(), attributes), "edit.createLine", drawLabels);
        attributes = new HashMap<AttributeKey,Object>();
        attributes.put(AttributeKeys.FILL_COLOR, Color.black);
        attributes.put(AttributeKeys.STROKE_COLOR, null);
        attributes = new HashMap<AttributeKey,Object>();
        attributes.put(AttributeKeys.FILL_COLOR, null);
        attributes.put(AttributeKeys.STROKE_COLOR, null);
    }
    /**
     * Creates toolbar buttons and adds them to the specified JToolBar
     */
    private void addAttributesButtonsTo(JToolBar bar, DrawingEditor editor) {
        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.draw.Labels");
        JButton b;
        
        b = bar.add(new PickAttributesAction(editor));
        b.setFocusable(false);
        b = bar.add(new ApplyAttributesAction(editor));
        b.setFocusable(false);
        bar.addSeparator();
        
        addColorButtonsTo(bar, editor);
        bar.addSeparator();
        addStrokeButtonsTo(bar, editor);
        bar.addSeparator();
        ButtonFactory.addFontButtonsTo(bar, editor);
    }
    private void addColorButtonsTo(JToolBar bar, DrawingEditor editor) {
        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.draw.Labels");
        HashMap<AttributeKey,Object> defaultAttributes = new HashMap<AttributeKey,Object>();
        STROKE_GRADIENT.set(defaultAttributes, (Gradient) null);
        bar.add(
                ButtonFactory.createEditorColorButton(editor,
                STROKE_COLOR, ButtonFactory.WEBSAVE_COLORS, ButtonFactory.WEBSAVE_COLORS_COLUMN_COUNT,
                "attribute.strokeColor", labels, 
                defaultAttributes
                )
                );
        defaultAttributes = new HashMap<AttributeKey,Object>();
        FILL_GRADIENT.set(defaultAttributes, (Gradient) null);
        bar.add(
                ButtonFactory.createEditorColorButton(editor,
                FILL_COLOR, ButtonFactory.WEBSAVE_COLORS, ButtonFactory.WEBSAVE_COLORS_COLUMN_COUNT,
                "attribute.fillColor", labels, 
                defaultAttributes
                )
                );
    }
    private void addStrokeButtonsTo(JToolBar bar, DrawingEditor editor) {
        bar.add(ButtonFactory.createStrokeWidthButton(editor));
        bar.add(ButtonFactory.createStrokeDashesButton(editor));
        bar.add(ButtonFactory.createStrokeCapButton(editor));
        bar.add(ButtonFactory.createStrokeJoinButton(editor));
    }
    /**
     * Creates toolbars for the application.
     */
    public java.util.List<JToolBar> createToolBars(Application a, View pr) {
        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.draw.Labels");
        ODGView p = (ODGView) pr;
        
        DrawingEditor editor;
        if (p == null) {
            editor = getSharedEditor();
        } else {
            editor = p.getEditor();
        }
        
        LinkedList<JToolBar> list = new LinkedList<JToolBar>();
        JToolBar tb;
        tb = new JToolBar();
        addCreationButtonsTo(tb, editor);
        tb.setName(labels.getString("window.drawToolBar.title"));
        list.add(tb);
        tb = new JToolBar();
        addAttributesButtonsTo(tb, editor);
        tb.setName(labels.getString("window.attributesToolBar.title"));
        list.add(tb);
        tb = new JToolBar();
        ButtonFactory.addAlignmentButtonsTo(tb, editor);
        tb.setName(labels.getString("window.alignmentToolBar.title"));
        list.add(tb);
        return list;
    }
    public void initView(Application a, View p) {
        if (a.isSharingToolsAmongViews()) {
            ((ODGView) p).setEditor(getSharedEditor());
        }
    }
    
    public void initApplication(Application a) {
        ResourceBundleUtil drawLabels = ResourceBundleUtil.getBundle("org.jhotdraw.draw.Labels");
        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.samples.svg.Labels");
        AbstractAction aa;
        
        putAction(ExportAction.ID, new ExportAction(a));
        putAction("view.toggleGrid", aa = new ToggleViewPropertyAction(a, ODGView.GRID_VISIBLE_PROPERTY));
        drawLabels.configureAction(aa, "view.toggleGrid");
        for (double sf : scaleFactors) {
            putAction((int) (sf*100)+"%",
                    aa = new ViewPropertyAction(a, "scaleFactor", Double.TYPE, new Double(sf))
                    );
            aa.putValue(Action.NAME, (int) (sf*100)+" %");
            
        }
        putAction("togglePropertiesPanel", new TogglePropertiesPanelAction(a));
    }
}
