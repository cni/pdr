function [data,fields,markers,cal,header] = eyeLoad(filename)
%
%
% [data,fields,markers,cal] = eyeLoad('/scratch/fMRI/phillips/s4/eye/eyeCal_20111212_122417.csv');
% data(strcmpi('NONE',markers),:) = []; markers(strcmpi('NONE',markers)) = [];
% gaze = eyeComputeGaze(data(:,3:4), cal);
% gaze(gaze>0.8)=NaN; gaze(gaze<-0.8)=NaN;
% figure(1);axis([-1,1,-1,1]); hold on;
% for(ii=1:size(gaze,1)), c='r'; plot(gaze(ii,1),gaze(ii,2),[c '.']); title(markers{ii}); pause(0.05); end
%
% [data,fields,markers] = eyeLoad('/scratch/fMRI/phillips/s4/eye/litAttn_20111212_123024.csv');
% gaze = eyeComputeGaze(data(strcmpi('start0',markers),3:4), cal);
% gaze(abs(gaze(:,1))>0.8|abs(gaze(:,2))>0.8|isnan(gaze(:,1))|isnan(gaze(:,2)),:)=NaN;
% figure(2);axis([-1,1,-1,1]); plot(gaze(500:1000,1),gaze(500:1000,2),'r-');
%
%
%
%

data = [];
fields = {};
header = {};
markers = {};
fid = fopen(filename, 'r');
aLine = fgetl(fid);
while(~isnumeric(aLine))
    %disp(aLine);
    [rowLabel,remainder] = strtok(aLine);
    if(~isnumeric(rowLabel))
        rowLabel = str2num(rowLabel);
    end
    if(rowLabel==5)
        while(~isempty(remainder))
            [fields{end+1},remainder] = strtok(remainder);
        end
    elseif(rowLabel==10)
        tmp = sscanf(remainder,'%f\t%f\t%f\t%f\t%f\t%f\t%f\t%f\t%f\t%d\t');
        data(end+1,:) = tmp;
        markers{end+1} = sscanf(remainder,'%*s\t%*s\t%*s\t%*s\t%*s\t%*s\t%*s\t%*s\t%*s\t%*s\t%s');
        if(markers{end}(1)=='"'&&markers{end}(end)=='"')
            markers{end} = markers{end}(2:end-1);
        end
    else
        header{end+1} = remainder;
    end
    aLine = fgetl(fid);
end
fclose(fid);

deltaTime = median(data(:,2))/1000;

calData = [];
for(ii=1:numel(markers))
    [tmp,n] = sscanf(markers{ii},'Cal(%f,%f)');
    if(n>0)
        calData(end+1,:) = [data(ii,3:4),tmp(:)'];
    end
end
if(~isempty(calData))
    [calPts,I,J] = unique(calData(:,3:4),'rows');
    for(ii=1:size(calPts,1))
        allEyePts = calData(J==ii,1:2);
        % reject the first 1 second of the readings
        firstGoodIndex = min(round(1/deltaTime), size(allEyePts,1)/2);
        allEyePts = allEyePts(firstGoodIndex:end, :);
        mn = mean(allEyePts);
        sd = std(allEyePts);
        z = [(mn(1)-allEyePts(:,1))./sd(1) (mn(2)-allEyePts(:,2))./sd(2)];
        bad = any(abs(z)>2,2);
        fprintf('Rejecting %d out of %d points for coord (%d,%d).\n',sum(bad),numel(bad),calPts(ii,:));
        eyePts(ii,:) = mean(allEyePts(~bad,:));
    end
    % Biquadratic mapping function with a piece-wise correction factor, introduce by
    % Sheena and Borah (1981), as described in D. Stampe (1993). Heuristic filtering
    % and reliable calibration methods for video-based pupil-tracking systems. B R M, I & C.
    corner = [1 3 7 9];
    center = [2 4 5 6 8];
    % Compute the bi-quadratic calibration matrix for all cal points except the four corners.
    cal.mat = pinv([eyePts(center,:) eyePts(center,:).^2 ones(numel(center),1)])*[calPts(center,:) ones(numel(center),1)];
    estCalPts = [eyePts(corner,:) eyePts(corner,:).^2 ones(numel(corner),1)]*cal.mat;
    estCalPts = estCalPts(:,1:2);
    % Use the four corners to compute the quadrant
    cal.quadScale = (calPts(corner,:)-estCalPts) ./ repmat(estCalPts(:,1).*estCalPts(:,2),1,2);
    cal.quadSign = sign(calPts(corner,:));
    estCalPts = eyeComputeGaze(eyePts, cal);
    [calPts estCalPts]

    calMat = pinv([eyePts ones(size(eyePts,1),1)])*[calPts ones(size(calPts,1),1)];
    estCalPts = [eyePts ones(size(eyePts,1),1)]*calMat;
    [calPts estCalPts(:,1:2)]

end
return;
