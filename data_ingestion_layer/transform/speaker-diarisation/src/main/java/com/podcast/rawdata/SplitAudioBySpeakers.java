package com.podcast.rawdata;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileWriter;
import java.io.InputStream;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.Arrays;

import edu.cmu.sphinx.speakerid.Segment;
import edu.cmu.sphinx.speakerid.SpeakerCluster;
import edu.cmu.sphinx.speakerid.SpeakerIdentification;

public class SplitAudioBySpeakers implements Runnable {
	int id;
	File audioFile;

	public SplitAudioBySpeakers(File audioFile, int i) {
		this.id = i;
		this.audioFile = audioFile;
	}

	public static String time(int milliseconds) {
		return (milliseconds / 60000) + ":" + (Math.round((double) (milliseconds % 60000) / 1000));
	}

	public void run() {
		try {
			String[] filePrefixArr = audioFile.getAbsolutePath().split("\\.");
			String[] filePrefixSplits = Arrays.copyOf(filePrefixArr, filePrefixArr.length - 1);
			String filePrefix = "";
			if (filePrefixSplits.length > 1) {
				filePrefix = String.join(".", filePrefixSplits);
			} else {
				filePrefix = filePrefixSplits[0];
			}
			String filename = filePrefix.split("/")[filePrefix.split("/").length - 1];
			String outPath = filePrefix + "#speakerSplits" + ".txt";

			System.out.println(filename + " processing started by thread id:" + id);

			SpeakerIdentification sd = new SpeakerIdentification();

			InputStream stream = new FileInputStream(new File(audioFile.getAbsolutePath()));

			ArrayList<SpeakerCluster> clusters = sd.cluster(stream);

			FileWriter fw = new FileWriter(outPath, true);
			BufferedWriter bw = new BufferedWriter(fw);
			PrintWriter out = new PrintWriter(bw);

			int idx = 0;
			for (SpeakerCluster spk : clusters) {
				idx++;

				ArrayList<Segment> segments = spk.getSpeakerIntervals();
				for (Segment seg : segments) {
					// only consider segments longer than 5 seconds
					if (seg.getLength() * 0.001 > 5.0) {
						out.println(
								filename + "\t" + time(seg.getStartTime()) + "\t" + time(seg.getLength()) + "\t" + idx);
					}
				}
			}
			out.close();

			System.out.println(filename + " processing completed by thread id:" + id);
		} catch (Exception err) {
			err.printStackTrace();
		}
	}
}

