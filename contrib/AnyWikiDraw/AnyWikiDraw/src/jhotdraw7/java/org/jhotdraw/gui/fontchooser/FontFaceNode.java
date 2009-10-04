/**
 * @(#)FontFaceNode.java
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
package org.jhotdraw.gui.fontchooser;

import java.awt.Font;
import java.util.Collections;
import java.util.Enumeration;
import javax.swing.tree.MutableTreeNode;
import javax.swing.tree.TreeNode;

/**
 * A FontFaceNode is a MutableTreeNode which does not allow children.
 *
 * @author Werner Randelshofer
 * @version $Id: FontFaceNode.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class FontFaceNode implements MutableTreeNode, Comparable<FontFaceNode>, Cloneable {

    private FontFamilyNode parent;
    private Font typeface;
    private String name;

    public FontFaceNode(Font typeface) {
        this.typeface = typeface;
        this.name = beautifyName(typeface.getPSName());
    }

    protected String beautifyName(String name) {
        // 'Beautify' the name
        int p = name.lastIndexOf('-');
        if (p != -1) {
            name = name.substring(p + 1);
            String lcName = name.toLowerCase();
            if (lcName.equals("plain")) {
                name = "Plain";
            } else if (lcName.equals("bolditalic")) {
                name = "Bold Italic";
            } else if (lcName.equals("italic")) {
                name = "Italic";
            } else if (lcName.equals("bold")) {
                name = "Bold";
            }
        } else {
            String lcName = name.toLowerCase();
            if (lcName.endsWith("plain")) {
                name = "Plain";
            } else if (lcName.endsWith("boldoblique")) {
                name = "Bold Oblique";
            } else if (lcName.endsWith("bolditalic")) {
                name = "Bold Italic";
            } else if (lcName.endsWith("bookita")) {
                name = "Book Italic";
            } else if (lcName.endsWith("bookit")) {
                name = "Book Italic";
            } else if (lcName.endsWith("demibold")) {
                name = "Demi Bold";
            } else if (lcName.endsWith("semiita")) {
                name = "Semi Italic";
            } else if (lcName.endsWith("italic")) {
                name = "Italic";
            } else if (lcName.endsWith("book")) {
                name = "Book";
            } else if (lcName.endsWith("bold")) {
                name = "Bold";
            } else if (lcName.endsWith("bol")) {
                name = "Bold";
            } else if (lcName.endsWith("oblique")) {
                name = "Oblique";
            } else if (lcName.endsWith("regular")) {
                name = "Regular";
            } else if (lcName.endsWith("semi")) {
                name = "Semi";
            } else {
                name = "Plain";
            }
        }
        StringBuilder buf = new StringBuilder();
        char prev = name.charAt(0);
        buf.append(prev);
        for (int i = 1; i < name.length(); i++) {
            char ch = name.charAt(i);
            if (prev != ' ' && prev != '-' &&
                    Character.isUpperCase(ch) && !Character.isUpperCase(prev) ||
                    Character.isDigit(ch) && !Character.isDigit(prev)) {
                buf.append(' ');
            }
            buf.append(ch);
            prev = ch;
        }
        name = buf.toString();
        return name;
    }

    public void setName(String newValue) {
        this.name = newValue;
    }

    public String getName() {
        return name;
    }

    public Font getFont() {
        return typeface;
    }

    @Override
    public String toString() {
        return name;
    }

    public void insert(MutableTreeNode child, int index) {
        throw new UnsupportedOperationException("Not allowed.");
    }

    public void remove(int index) {
        throw new UnsupportedOperationException("Not allowed.");
    }

    public void remove(MutableTreeNode node) {
        throw new UnsupportedOperationException("Not allowed.");
    }

    public void setUserObject(Object object) {
        throw new UnsupportedOperationException("Not allowed.");
    }

    public void removeFromParent() {
        if (parent != null) {
            parent.remove(this);
        }
    }

    public void setParent(MutableTreeNode newParent) {
        this.parent = (FontFamilyNode) newParent;
    }

    public TreeNode getChildAt(int childIndex) {
        throw new IndexOutOfBoundsException("" + childIndex);
    }

    public int getChildCount() {
        return 0;
    }

    public TreeNode getParent() {
        return parent;
    }

    public int getIndex(TreeNode node) {
        return -1;
    }

    public boolean getAllowsChildren() {
        return false;
    }

    public boolean isLeaf() {
        return true;
    }

    @SuppressWarnings("unchecked")
    public Enumeration children() {
        return Collections.enumeration(Collections.EMPTY_LIST);
    }

    public int compareTo(FontFaceNode that) {
        return this.name.compareTo(that.name);
    }

    @Override
    public FontFaceNode clone() {
        FontFaceNode that;
        try {
            that = (FontFaceNode) super.clone();
        } catch (CloneNotSupportedException ex) {
            InternalError error = new InternalError("Clone failed");
            error.initCause(ex);
            throw error;
        }
        that.parent = null;
        return that;
    }

    public boolean isEditable() {
        return false;
    }
}
