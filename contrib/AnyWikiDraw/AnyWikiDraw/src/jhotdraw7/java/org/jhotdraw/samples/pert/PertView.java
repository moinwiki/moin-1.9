/*
 * @(#)PertView.java
 *
 * Copyright (c) 1996-2007 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 *
 */
package org.jhotdraw.samples.pert;

import java.awt.print.Pageable;
import java.util.*;
import org.jhotdraw.gui.*;
import org.jhotdraw.io.*;
import org.jhotdraw.undo.*;
import org.jhotdraw.util.*;
import java.awt.*;
import java.beans.*;
import java.io.*;
import java.lang.reflect.*;
import javax.swing.*;
import javax.swing.border.*;
import org.jhotdraw.app.*;
import org.jhotdraw.app.action.*;
import org.jhotdraw.draw.*;
import org.jhotdraw.draw.action.*;

/**
 * A view for Pert diagrams.
 *
 * @author Werner Randelshofer
 * @version $Id: PertView.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class PertView extends AbstractView {
    public final static String GRID_VISIBLE_PROPERTY = "gridVisible";
   
    /**
     * Each view uses its own undo redo manager.
     * This allows for undoing and redoing actions per view.
     */
    private UndoRedoManager undo;
    
    /**
     * Depending on the type of an application, there may be one editor per
     * view, or a single shared editor for all views.
     */
    private DrawingEditor editor;
    
    /**
     * Creates a new view.
     */
    public PertView() {
    }
    
    /**
     * Initializes the view.
     */
    public void init() {
        super.init();
        
        initComponents();
        
        JPanel zoomButtonPanel = new JPanel(new BorderLayout());
        scrollPane.setLayout(new PlacardScrollPaneLayout());
        scrollPane.setBorder(new EmptyBorder(0,0,0,0));
        
        setEditor(new DefaultDrawingEditor());
        undo = new UndoRedoManager();
        view.setDrawing(createDrawing());
        view.getDrawing().addUndoableEditListener(undo);
        initActions();
        undo.addPropertyChangeListener(new PropertyChangeListener() {
            public void propertyChange(PropertyChangeEvent evt) {
                setHasUnsavedChanges(undo.hasSignificantEdits());
            }
        });
        
        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.draw.Labels");
        
        JPanel placardPanel = new JPanel(new BorderLayout());
        javax.swing.AbstractButton pButton;
        pButton = ButtonFactory.createZoomButton(view);
        pButton.putClientProperty("Quaqua.Button.style","placard");
        pButton.putClientProperty("Quaqua.Component.visualMargin",new Insets(0,0,0,0));
        pButton.setFont(UIManager.getFont("SmallSystemFont"));
        placardPanel.add(pButton, BorderLayout.WEST);
        pButton = ButtonFactory.createToggleGridButton(view);
        pButton.putClientProperty("Quaqua.Button.style","placard");
        pButton.putClientProperty("Quaqua.Component.visualMargin",new Insets(0,0,0,0));
        pButton.setFont(UIManager.getFont("SmallSystemFont"));
        labels.configureToolBarButton(pButton, "view.toggleGrid.placard");
        placardPanel.add(pButton, BorderLayout.EAST);
        scrollPane.add(placardPanel, JScrollPane.LOWER_LEFT_CORNER);

        setGridVisible(preferences.getBoolean("view.gridVisible", false));
        setScaleFactor(preferences.getDouble("view.scaleFactor", 1d));
    }
    
    /**
     * Creates a new Drawing for this view.
     */
    protected Drawing createDrawing() {
        DefaultDrawing drawing = new DefaultDrawing();
        DOMStorableInputOutputFormat ioFormat =
                new DOMStorableInputOutputFormat(new PertFactory());
        LinkedList<InputFormat> inputFormats = new LinkedList<InputFormat>();
        inputFormats.add(ioFormat);
        drawing.setInputFormats(inputFormats);
        LinkedList<OutputFormat> outputFormats = new LinkedList<OutputFormat>();
        outputFormats.add(ioFormat);
        outputFormats.add(new ImageOutputFormat());
        drawing.setOutputFormats(outputFormats);
        return drawing;
    }
    /**
     * Creates a Pageable object for printing this view.
     */
    public Pageable createPageable() {
        return new DrawingPageable(view.getDrawing());
        
    }
    
    public DrawingEditor getEditor() {
        return editor;
    }
    public void setEditor(DrawingEditor newValue) {
        DrawingEditor oldValue = editor;
        if (oldValue != null) {
            oldValue.remove(view);
        }
        editor = newValue;
        if (newValue != null) {
            newValue.add(view);
        }
    }
    
    public void setGridVisible(boolean newValue) {
        boolean oldValue = isGridVisible();
        view.setConstrainerVisible(newValue);
        firePropertyChange(GRID_VISIBLE_PROPERTY, oldValue, newValue);
        preferences.putBoolean("view.gridVisible", newValue);
    }
    public boolean isGridVisible() {
       return view.isConstrainerVisible();
    }
    public double getScaleFactor() {
       return view.getScaleFactor();
    }
    public void setScaleFactor(double newValue) {
        double oldValue = getScaleFactor();
        view.setScaleFactor(newValue);
        
        firePropertyChange("scaleFactor", oldValue, newValue);
        preferences.putDouble("view.scaleFactor", newValue);
    }
    /**
     * Initializes view specific actions.
     */
    private void initActions() {
        putAction(UndoAction.ID, undo.getUndoAction());
        putAction(RedoAction.ID, undo.getRedoAction());
    }
    protected void setHasUnsavedChanges(boolean newValue) {
        super.setHasUnsavedChanges(newValue);
        undo.setHasSignificantEdits(newValue);
    }
    
    /**
     * Writes the view to the specified file.
     */
    public void write(File f) throws IOException {
            Drawing drawing = view.getDrawing();
            OutputFormat outputFormat = drawing.getOutputFormats().get(0);
            outputFormat.write(f, drawing);
    }
    
    /**
     * Reads the view from the specified file.
     */
    public void read(File f) throws IOException {
        try {
            final Drawing drawing = createDrawing();
            InputFormat inputFormat = drawing.getInputFormats().get(0);
            inputFormat.read(f, drawing, true);
            SwingUtilities.invokeAndWait(new Runnable() { public void run() {
                view.getDrawing().removeUndoableEditListener(undo);
                view.setDrawing(drawing);
                view.getDrawing().addUndoableEditListener(undo);
                undo.discardAllEdits();
            }});
        } catch (InterruptedException e) {
            InternalError error = new InternalError();
            e.initCause(e);
            throw error;
        } catch (InvocationTargetException e) {
            InternalError error = new InternalError();
            e.initCause(e);
            throw error;
        }
    }
    
    /**
     * Clears the view.
     */
    public void clear() {
        final Drawing newDrawing = createDrawing();
        try {
            SwingUtilities.invokeAndWait(new Runnable() {
                public void run() {
                    view.getDrawing().removeUndoableEditListener(undo);
                    view.setDrawing(newDrawing);
                    view.getDrawing().addUndoableEditListener(undo);
                    undo.discardAllEdits();
                }
            });
        } catch (InvocationTargetException ex) {
            ex.printStackTrace();
        } catch (InterruptedException ex) {
            ex.printStackTrace();
        }
    }
    
    @Override protected JFileChooser createOpenChooser() {
        JFileChooser c = new JFileChooser();
        c.addChoosableFileFilter(new ExtensionFileFilter("Pert Diagram","xml"));
        if (preferences != null) {
            c.setSelectedFile(new File(preferences.get("projectFile", System.getProperty("user.home"))));
        }
        return c;
    }
    @Override protected JFileChooser createSaveChooser() {
        JFileChooser c = new JFileChooser();
        c.addChoosableFileFilter(new ExtensionFileFilter("Pert Diagram","xml"));
        if (preferences != null) {
            c.setSelectedFile(new File(preferences.get("projectFile", System.getProperty("user.home"))));
        }
        return c;
    }
    @Override
    public boolean canSaveTo(File file) {
        return file.getName().endsWith(".xml");
    }
    
    /** This method is called from within the constructor to
     * initialize the form.
     * WARNING: Do NOT modify this code. The content of this method is
     * always regenerated by the Form Editor.
     */
    // <editor-fold defaultstate="collapsed" desc="Generated Code">//GEN-BEGIN:initComponents
    private void initComponents() {

        scrollPane = new javax.swing.JScrollPane();
        view = new org.jhotdraw.draw.DefaultDrawingView();

        setLayout(new java.awt.BorderLayout());

        scrollPane.setHorizontalScrollBarPolicy(javax.swing.ScrollPaneConstants.HORIZONTAL_SCROLLBAR_ALWAYS);
        scrollPane.setVerticalScrollBarPolicy(javax.swing.ScrollPaneConstants.VERTICAL_SCROLLBAR_ALWAYS);
        scrollPane.setViewportView(view);

        add(scrollPane, java.awt.BorderLayout.CENTER);
    }// </editor-fold>//GEN-END:initComponents
    
    
    // Variables declaration - do not modify//GEN-BEGIN:variables
    private javax.swing.JScrollPane scrollPane;
    private org.jhotdraw.draw.DefaultDrawingView view;
    // End of variables declaration//GEN-END:variables
    
}
