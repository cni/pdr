function gaze = eyeComputeGaze(rawCoords, cal)
%
%

gaze = [rawCoords rawCoords.^2 ones(size(rawCoords,1),1)] * cal.mat;
gaze = gaze(:,1:2);
[junk,quad] = ismember(sign(gaze),cal.quadSign,'rows');
gaze = gaze + cal.quadScale(quad,:).*repmat(gaze(:,1).*gaze(:,2),1,2);

return;


