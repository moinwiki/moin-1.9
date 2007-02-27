package CH.ifa.draw.twiki;
import java.awt.*;
import java.awt.event.*;
///import java.awt.image.*;
import java.util.*;
import java.io.*;
import java.net.*;

public class TestFrame extends Frame
{
	private Image image = null;

	public TestFrame()
	{
		super();
	}

	public TestFrame(String title)
	{
		super(title);
	}

	public void setImage(Image theImage)
	{
		image = theImage;
		MediaTracker tracker = new MediaTracker(this);
		tracker.addImage(theImage, 0);
		try {
			tracker.waitForAll();
		} catch (Exception e) {  }
	}

	public void paint(Graphics g)
	{
		if(image != null) {
			g.drawImage(image, 0, 20, this);
		}
//		g.setColor(Color.red);
//		g.fillOval(0, 20, 32, 52);
	}

	public void update(Graphics g)
	{
		paint(g);
	}
}
