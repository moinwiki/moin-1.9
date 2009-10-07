/*
 * @(#)TeddyView.java
 *
 * Copyright (c) 2006 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and
 * contributors of the JHotDraw project ("the copyright holders").
 * You may not use, copy or modify this software, except in
 * accordance with the license agreement you entered into with
 * the copyright holders. For details see accompanying license terms.
 */

package org.jhotdraw.samples.teddy;

import java.awt.event.*;
import org.jhotdraw.app.*;
import org.jhotdraw.samples.teddy.text.*;
import org.jhotdraw.samples.teddy.regex.*;
import org.jhotdraw.undo.*;
import org.jhotdraw.samples.teddy.io.*;
import java.lang.reflect.*;
import java.awt.*;
import java.beans.*;
import java.util.prefs.*;
import javax.swing.*;
import javax.swing.event.*;
import javax.swing.text.*;
import javax.swing.undo.*;
import java.io.*;
import org.jhotdraw.app.action.RedoAction;
import org.jhotdraw.app.action.UndoAction;
import org.jhotdraw.util.prefs.PreferencesUtil;

/**
 * TeddyView.
 *
 * @author Werner Randelshofer
 * @version $Id: TeddyView.java 529 2009-06-08 21:12:23Z rawcoder $
*/
public class TeddyView extends AbstractView {
    private static Preferences prefs = PreferencesUtil.userNodeForPackage(TeddyView.class);
    
    protected JTextPane editor;
    
    private static class EditorPanel extends JPanel implements Scrollable {
        private JTextComponent editor;
        private boolean isLineWrap;
        
        public void setEditor(JTextComponent newValue) {
            editor = newValue;
            removeAll();
            setLayout(new BorderLayout());
            add(editor);
            setBackground(UIManager.getColor("TextField.background"));
            setOpaque(true);
        }
        public void setLineWrap(boolean newValue) {
            isLineWrap = newValue;
            editor.revalidate();
            editor.repaint();
        }
        public boolean getLineWrap() {
            return isLineWrap;
        }
        
        public Dimension getPreferredScrollableViewportSize() {
            // System.out.println("EditorViewport: "+editor.getPreferredScrollableViewportSize());
            return editor.getPreferredScrollableViewportSize();
        }
        
        public int getScrollableUnitIncrement(Rectangle visibleRect, int orientation, int direction) {
            return editor.getScrollableUnitIncrement(visibleRect, orientation, direction);
        }
        
        public int getScrollableBlockIncrement(Rectangle visibleRect, int orientation, int direction) {
            return editor.getScrollableBlockIncrement(visibleRect, orientation, direction);
        }
        
        public boolean getScrollableTracksViewportWidth() {
            return isLineWrap;
        }
        
        public boolean getScrollableTracksViewportHeight() {
            return editor.getScrollableTracksViewportHeight();
        }
    }
    
    protected EditorPanel editorViewport;
    
    /**
     * The undo/redo manager.
     */
    protected UndoRedoManager undoManager;
    
    /**
     * The panel used for the find feature.
     */
    private FindDialog findDialog;
    /**
     * The Matcher used to perform find operation.
     */
    private Matcher matcher;
    private CharacterSetAccessory characterSetAccessory;
    
    
    /** Creates a new instance. */
    public TeddyView() {
        prefs = PreferencesUtil.userNodeForPackage(TeddyView.class);
    }
    
    protected JTextPane createEditor() {
        return new JTextPane();
    }
    
    public void init() {
        initComponents();
        
        editor = createEditor();
        editorViewport = new EditorPanel();
        editorViewport.setEditor(editor);
        scrollPane.setViewportView(editorViewport);
        editor.addCaretListener(new CaretListener() {
            public void caretUpdate(CaretEvent evt) {
                TeddyView.this.caretUpdate(evt);
            }
        });
        scrollPane.getViewport().setBackground(editor.getBackground());
        scrollPane.getViewport().addMouseListener(new MouseAdapter() {
            @Override public void mousePressed(MouseEvent evt) {
                editor.requestFocus();
            }
        });
        
        Font font = getFont();
        MutableAttributeSet attrs = ((StyledEditorKit) editor.getEditorKit()).getInputAttributes();
        StyleConstants.setFontFamily(attrs, font.getFamily());
        StyleConstants.setFontSize(attrs, font.getSize());
        StyleConstants.setItalic(attrs, (font.getStyle() & Font.ITALIC) != 0);
        StyleConstants.setBold(attrs, (font.getStyle() & Font.BOLD) != 0);
        
        // Init preferences
        statusBar.setVisible(prefs.getBoolean("statusBarVisible", false));
        editorViewport.setLineWrap(prefs.getBoolean("lineWrap", true));
        
        NumberedEditorKit editorKit = new NumberedEditorKit();
        ((NumberedViewFactory) editorKit.getViewFactory()).
                setLineNumbersVisible(prefs.getBoolean("lineNumbersVisible", false));
        editor.setEditorKit(editorKit);
        editor.setDocument(createDocument());
        
        
        setPreferredSize(new Dimension(400, 400));
        
        undoManager = new UndoRedoManager();
        editor.getDocument().addUndoableEditListener(undoManager);
        undoManager.addPropertyChangeListener(new PropertyChangeListener() {
            public void propertyChange(PropertyChangeEvent evt) {
                setHasUnsavedChanges(undoManager.hasSignificantEdits());
            }
        });
        initActions();
    }
    
    
    public void setEnabled(boolean newValue) {
        super.setEnabled(newValue);
        editor.setEnabled(newValue);
        scrollPane.setEnabled(newValue);
    }
    
    public void setStatusBarVisible(boolean newValue) {
        boolean oldValue = statusBar.isVisible();
        statusBar.setVisible(newValue);
        prefs.putBoolean("statusBarVisible", newValue);
        firePropertyChange("statusBarVisible", oldValue, newValue);
    }
    public boolean isStatusBarVisible() {
        return statusBar.isVisible();
    }
    public void setLineWrap(boolean newValue) {
        boolean oldValue = editorViewport.getLineWrap();
        editorViewport.setLineWrap(newValue);
        prefs.putBoolean("lineWrap", newValue);
        firePropertyChange("lineWrap", oldValue, newValue);
    }
    public boolean isLineWrap() {
        return editorViewport.getLineWrap();
    }
    
    private void initActions() {
        putAction(UndoAction.ID, undoManager.getUndoAction());
        putAction(RedoAction.ID, undoManager.getRedoAction());
    }
    
    private CharacterSetAccessory getAccessory() {
        if (characterSetAccessory == null) {
            characterSetAccessory = new CharacterSetAccessory();
        }
        return characterSetAccessory;
    }
    @Override
    public JFileChooser getOpenChooser() {
        JFileChooser chooser = super.getOpenChooser();
        chooser.setAccessory(getAccessory());
        return chooser;
    }
    @Override
    public JFileChooser getSaveChooser() {
        JFileChooser chooser = super.getSaveChooser();
        chooser.setAccessory(getAccessory());
        return chooser;
    }
    public void read(File f) throws IOException {
        read(f, getAccessory().getCharacterSet());
    }
    public void read(File f, String characterSet) throws IOException {
        final Document doc = readDocument(f, characterSet);
        try {
            SwingUtilities.invokeAndWait(new Runnable() {
                public void run() {
                    editor.getDocument().removeUndoableEditListener(undoManager);
                    editor.setDocument(doc);
                    doc.addUndoableEditListener(undoManager);
                    undoManager.discardAllEdits();
                }
            });
        } catch (InterruptedException e) {
            // ignore
        } catch (InvocationTargetException e) {
            InternalError error = new InternalError(e.getMessage());
            error.initCause(e);
            throw error;
        }
    }
    public void write(File f) throws IOException {
        write(f, getAccessory().getCharacterSet(), getAccessory().getLineSeparator());
    }
    public void write(File f, String characterSet, String lineSeparator) throws IOException {
        writeDocument(editor.getDocument(), f, characterSet, lineSeparator);
        try {
            SwingUtilities.invokeAndWait(new Runnable() {
                public void run() {
                    undoManager.setHasSignificantEdits(false);
                }
            });
        } catch (InterruptedException e) {
            // ignore
        } catch (InvocationTargetException e) {
            InternalError error = new InternalError(e.getMessage());
            error.initCause(e);
            throw error;
        }
    }
    
    /**
     * Reads a document from a file using the specified character set.
     */
    private Document readDocument(File f, String characterSet)
    throws IOException {
        ProgressMonitorInputStream pin = new ProgressMonitorInputStream(this, "Reading "+f.getName(), new FileInputStream(f));
        BufferedReader in = new BufferedReader(new InputStreamReader(pin, characterSet));
        try {
            
            // PlainDocument doc = new PlainDocument();
            StyledDocument doc = createDocument();
            MutableAttributeSet attrs = ((StyledEditorKit) editor.getEditorKit()).getInputAttributes();
            String line;
            boolean isFirst = true;
            while ((line = in.readLine()) != null) {
                if (isFirst) {
                    isFirst = false;
                } else {
                    doc.insertString(doc.getLength(), "\n", attrs);
                }
                doc.insertString(doc.getLength(), line, attrs);
            }
            return doc;
        } catch (BadLocationException e) {
            throw new IOException(e.getMessage());
        } catch (OutOfMemoryError e) {
            System.err.println("out of memory!");
            throw new IOException("Out of memory.");
        } finally {
            in.close();
        }
    }
    
    public void clear() {
        final Document newDocument = createDocument();
        try {
            SwingUtilities.invokeAndWait(new Runnable() {
                public void run() {
                    editor.getDocument().removeUndoableEditListener(undoManager);
                    editor.setDocument(newDocument);
                    editor.getDocument().addUndoableEditListener(undoManager);
                    setHasUnsavedChanges(false);
                }
            });
        } catch (InvocationTargetException ex) {
            ex.printStackTrace();
        } catch (InterruptedException ex) {
            ex.printStackTrace();
        }
    }
    
    protected StyledDocument createDocument() {
        DefaultStyledDocument doc = new DefaultStyledDocument();
        doc.setParagraphAttributes(0, 1, ((StyledEditorKit) editor.getEditorKit()).getInputAttributes(), true);
        return doc;
    }
    
    
    /**
     * Writes a document into a file using the specified character set.
     */
    private void writeDocument(Document doc, File f, String characterSet, String lineSeparator)
    throws IOException {
        LFWriter out = new LFWriter(new OutputStreamWriter(new FileOutputStream(f), characterSet));
        out.setLineSeparator(lineSeparator);
        try {
            String sequence;
            for (int i=0; i < doc.getLength(); i+=256) {
                out.write(doc.getText(i, Math.min(256, doc.getLength() - i)));
            }
        } catch (BadLocationException e) {
            throw new IOException(e.getMessage());
        } finally {
            out.close();
            undoManager.discardAllEdits();
        }
    }
    
    
    /** This method is called from within the constructor to
     * initialize the form.
     * WARNING: Do NOT modify this code. The content of this method is
     * always regenerated by the Form Editor.
     */
    // <editor-fold defaultstate="collapsed" desc="Generated Code">//GEN-BEGIN:initComponents
    private void initComponents() {

        statusBar = new javax.swing.JPanel();
        caretInfoLabel = new javax.swing.JLabel();
        scrollPane = new javax.swing.JScrollPane();

        setLayout(new java.awt.BorderLayout());

        statusBar.setLayout(new java.awt.BorderLayout());

        caretInfoLabel.setFont(new java.awt.Font("Lucida Grande", 0, 11));
        caretInfoLabel.setText("1:1");
        caretInfoLabel.setBorder(javax.swing.BorderFactory.createEmptyBorder(1, 3, 0, 3));
        statusBar.add(caretInfoLabel, java.awt.BorderLayout.CENTER);

        add(statusBar, java.awt.BorderLayout.SOUTH);

        scrollPane.setBorder(null);
        scrollPane.setVerticalScrollBarPolicy(javax.swing.ScrollPaneConstants.VERTICAL_SCROLLBAR_ALWAYS);
        add(scrollPane, java.awt.BorderLayout.CENTER);
    }// </editor-fold>//GEN-END:initComponents
    
    public Document getDocument() {
        return editor.getDocument();
    }
    
    
    /**
     * Accessor for text area.
     * This is used by Actions that need ot act on the text area of the View.
     */
    public void select(int start, int end) {
        editor.select(start, end);
        try {
            editor.scrollRectToVisible(editor.modelToView(start));
        } catch (BadLocationException e) {
            e.printStackTrace();
        }
    }
    
    /**
     * Accessor for text area.
     * This is used by Actions that need ot act on the text area of the View.
     */
    public int getSelectionStart() {
        return editor.getSelectionStart();
    }
    /**
     * Accessor for text area.
     * This is used by Actions that need ot act on the project text area.
     */
    public int getSelectionEnd() {
        return editor.getSelectionEnd();
    }
    /**
     * Determines the number of lines contained in the area.
     *
     * @return the number of lines > 0
     */
    public int getLineCount() {
        Element map = getDocument().getDefaultRootElement();
        return map.getElementCount();
    }
    /**
     * Accessor for text area.
     * This is used by Actions that need to act on the text area of the View.
     */
    public void replaceRange(String str, int start, int end) {
        //editor.replaceRange(str, start, end);
        if (end < start) {
            throw new IllegalArgumentException("end before start");
        }
        Document doc = getDocument();
        if (doc != null) {
            try {
                if (doc instanceof AbstractDocument) {
                    ((AbstractDocument)doc).replace(start, end - start, str,
                            null);
                } else {
                    doc.remove(start, end - start);
                    doc.insertString(start, str, null);
                }
            } catch (BadLocationException e) {
                throw new IllegalArgumentException(e.getMessage());
            }
        }
    }
    
    /**
     * Accessor for text area.
     * This is used by Actions that need ot act on the text area of the View.
     */
    public int getLineOfOffset(int offset) throws BadLocationException {
        //return editor.getLineOfOffset(offset);
        Document doc = getDocument();
        if (offset < 0) {
            throw new BadLocationException("Can't translate offset to line", -1);
        } else if (offset > doc.getLength()) {
            throw new BadLocationException("Can't translate offset to line", doc.getLength()+1);
        } else {
            Element map = getDocument().getDefaultRootElement();
            return map.getElementIndex(offset);
        }
    }
    /**
     * Accessor for text area.
     * This is used by Actions that need ot act on the text area of the View.
     */
    public int getLineStartOffset(int line) throws BadLocationException {
        //return editor.getLineStartOffset(line);
        int lineCount = getLineCount();
        if (line < 0) {
            throw new BadLocationException("Negative line", -1);
        } else if (line >= lineCount) {
            throw new BadLocationException("No such line", getDocument().getLength()+1);
        } else {
            Element map = getDocument().getDefaultRootElement();
            Element lineElem = map.getElement(line);
            return lineElem.getStartOffset();
        }
    }
    
    public void fireEdit(UndoableEdit edit) {
        undoManager.addEdit(edit);
    }
    
    private void caretUpdate(javax.swing.event.CaretEvent evt) {
        try {
            int pos = editor.getCaretPosition();
            int line = getLineOfOffset(pos);
            int lineStartOffset = getLineStartOffset(line);
            caretInfoLabel.setText((line + 1)+":"+(pos - lineStartOffset + 1));
        } catch (BadLocationException e) {
            caretInfoLabel.setText(e.toString());
        }
    }
    
    public void setLineNumbersVisible(boolean newValue) {
        NumberedViewFactory viewFactory = (NumberedViewFactory) editor.
                getEditorKit().
                getViewFactory();
        boolean oldValue = viewFactory.isLineNumbersVisible();
        if (oldValue != newValue) {
            viewFactory.setLineNumbersVisible(newValue);
            prefs.putBoolean("lineNumbersVisible", newValue);
            firePropertyChange("lineNumbersVisible", oldValue, newValue);
            editor.revalidate();
            editor.repaint();
        }
        
    }
    public boolean isLineNumbersVisible() {
        NumberedViewFactory viewFactory = (NumberedViewFactory) editor.
                getEditorKit().
                getViewFactory();
        return viewFactory.isLineNumbersVisible();
    }
    
    
    // Variables declaration - do not modify//GEN-BEGIN:variables
    public javax.swing.JLabel caretInfoLabel;
    public javax.swing.JScrollPane scrollPane;
    public javax.swing.JPanel statusBar;
    // End of variables declaration//GEN-END:variables
    
}
