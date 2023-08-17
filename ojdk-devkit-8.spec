%global centos5_arches x86_64 %ix86
%global centos7_altarches aarch64 ppc64 ppc64le %arm
# we do not want debug packages
%global debug_package %{nil}

Name: ojdk-devkit-8
Version: 0.1
Release: 1%{?dist}
Summary: OpenJDK devkit 8

# License TODO: should include license of all rpms unpacked to sysroot?
License: GPLv2
URL: http://openjdk.java.net/
Source0: https://github.com/openjdk/jdk8u/archive/refs/tags/jdk8u382-ga.tar.gz

BuildRequires: make autoconf automake libtool gcc gcc-c++ wget glibc-devel texinfo tar
%ifarch x86_64
BuildRequires: glibc-devel(x86-32) libgcc(x86-32) libstdc++-devel(x86-32)
%endif
# for testing
BuildRequires: java-1.8.0-openjdk-devel
# curently no requires
#Requires:

%description
OpenJDK devkit 8

%prep
%setup -q -n jdk8u-jdk8u382-ga

# fix mpc download link
sed -i 's;http://www.multiprecision.org/mpc/download/;https://ftp.gnu.org/gnu/mpc/;g' make/devkit/Tools.gmk

# use CentOS packages with fallback to Fedora
pushd make/devkit
cat Tools.gmk | sed -n  '/^RPM_LIST/,/^$/p' > dlrpms.mk
echo 'ARCH := $(shell uname -m)' >> dlrpms.mk
echo 'BASE_URL := https://archives.fedoraproject.org/pub/archive/fedora-secondary/releases/19/Everything/$(ARCH)/os/Packages/' >> dlrpms.mk
%ifarch %{centos5_arches}
# CentOS5 packages are only available on x86_64, i386
sed -i 's;^BASE_URL :=.*;BASE_URL := https://vault.centos.org/5.11/os/$(ARCH)/CentOS/;g' dlrpms.mk
%endif
%ifarch %{centos7_altarches}
# CentOS7 (altarch) packages are available on aarch64, ppc64, ppc64le arm
sed -i 's;^BASE_URL :=.*;BASE_URL := https://vault.centos.org/altarch/7.8.2003/os/$(ARCH)/Packages/;g' dlrpms.mk
%endif
echo 'download-rpms:' >> dlrpms.mk
echo '	mkdir rpms' >> dlrpms.mk
# trick from devkit of later jdks
echo '	wget -r -e robots=off -P rpms -np -nd $(patsubst %%, -A "*%%*.rpm", $(RPM_LIST)) $(BASE_URL)' >> dlrpms.mk
%ifarch x86_64
# x86_64 devkit also wants i386 packages, x86_64 repo also contains these, but *-headers packages are missing (required for gcc build)
# echo '	wget -r -e robots=off -P rpms -np -nd -A "*kernel-headers*.rpm" -A "*glibc-headers*.rpm" -A "*compat-glibc-headers*.rpm" https://vault.centos.org/5.11/os/i386/CentOS/' >> dlrpms.mk
%endif
cat dlrpms.mk
make -f dlrpms.mk download-rpms
%ifarch x86_64
# x86_64 devkit also wants i386 packages, x86_64 repo also contains these,
# but *-headers packages are missing required for gcc build,
# x86_64 ones are universal (multilib) -> just make a copy as i386
for file in rpms/*headers*.x86_64.rpm ; do
	file386="${file%.x86_64.rpm}.i386.rpm"
	file686="${file%.x86_64.rpm}.i686.rpm"
	if ! [ -e "${file386}" ] && ! [ -e "${file686}" ] ; then
		cp "${file}" "${file386}"
	fi
done
%endif
ls rpms
popd

%build
pushd make/devkit
make RPM_DIR="$(pwd)/rpms" all tars
popd

%install
mkdir -p %{buildroot}%{_datadir}/%{name}
cp -p build/devkit/result/*.tar.gz %{buildroot}%{_datadir}/%{name}/

%check
# check if jdk can be build using devkit
mkdir devkit
tar -C devkit --strip-components=1 -xf %{buildroot}%{_datadir}/%{name}/*.tar.gz
rm -rf build
bash configure --with-devkit="$(pwd)/devkit" --with-boot-jdk=/usr/lib/jvm/java-1.8.0-openjdk
make images
build/*/images/jdk/bin/java -version

%files
%{_datadir}/%{name}

%changelog
