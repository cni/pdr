function [data,fields,header,calMat,markers] = eyeLoad(filename)
%
%
% [data,fields,header,calMat,markers] = eyeLoad('eyeCal_20111212_122417.csv');
% data(strcmpi('NONE',markers),:) = []; markers(strcmpi('NONE',markers)) = [];
% gaze = [data(:,3:4) ones(size(data,1),1)]*calMat;
% gaze = gaze(:,1:2); gaze(gaze>1)=1; gaze(gaze<-1)=-1;
% figure(1);axis([-1,1,-1,1]); hold on;
% for(ii=1:size(gaze,1)), if(data(ii,8)>0.5), c='r'; else, c='y'; end; plot(gaze(ii,1),gaze(ii,2),[c '.']); title(markers{ii}); pause(0.1); end
%
% [data,fields] = eyeLoad('litAttn_20111212_123024.csv');
%
%
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
    calMat = pinv([eyePts ones(size(eyePts,1),1)])*[calPts ones(size(calPts,1),1)];

    calPts
    estCalPts = [eyePts ones(size(eyePts,1),1)]*calMat;
    estCalPts(:,1:2)
end
return;
